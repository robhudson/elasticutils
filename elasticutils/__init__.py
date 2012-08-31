import logging
from itertools import izip
from operator import itemgetter

from pyes import ES
from pyes import VERSION as PYES_VERSION

from elasticutils._version import __version__


log = logging.getLogger('elasticutils')


DEFAULT_HOSTS = ['localhost:9200']
DEFAULT_TIMEOUT = 5
DEFAULT_DOCTYPES = None
DEFAULT_INDEXES = 'default'
DEFAULT_DUMP_CURL = None


def _split(s):
    if '__' in s:
        return s.rsplit('__', 1)
    return s, None


def get_es(hosts=None, default_indexes=None, timeout=None, dump_curl=None,
           **settings):
    """Create an ES object and return it.

    :arg hosts: list of uris; ES hosts to connect to, defaults to
        ``['localhost:9200']``
    :arg default_indexes: list of strings; the default indexes to use,
        defaults to 'default'
    :arg timeout: int; the timeout in seconds, defaults to 5
    :arg dump_curl: function or None; function that dumps curl output,
        see docs, defaults to None
    :arg settings: other settings to pass into `pyes.es.ES`

    Examples:

    >>> get_es()
    >>> get_es(hosts=['localhost:9200'])
    >>> get_es(timeout=30)  # good for indexing
    >>> get_es(default_indexes=['sumo_prod_20120627']
    >>> class CurlDumper(object):
    ...     def write(self, text):
    ...         print text
    ...
    >>> get_es(dump_curl=CurlDumper())

    """
    # Cheap way of de-None-ifying things
    hosts = hosts or DEFAULT_HOSTS
    default_indexes = default_indexes or DEFAULT_INDEXES
    timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    dump_curl = dump_curl or DEFAULT_DUMP_CURL

    if not isinstance(default_indexes, list):
        default_indexes = [default_indexes]

    es = ES(hosts,
            default_indexes=default_indexes,
            timeout=timeout,
            dump_curl=dump_curl,
            **settings)

    # pyes 0.15 does this lame thing where it ignores dump_curl in
    # the ES constructor and always sets it to None. So what we do
    # is set it manually after the ES has been created and
    # defaults['dump_curl'] is truthy. This might not work for all
    # values of dump_curl.
    if PYES_VERSION[0:2] == (0, 15) and dump_curl is not None:
        es.dump_curl = dump_curl

    return es


class InvalidFieldActionError(Exception):
    """Raise this when the field action doesn't exist"""
    pass


def _process_filters(filters):
    rv = []
    for f in filters:
        if isinstance(f, F):
            if f.filters:
                rv.append(f.filters)
        else:
            key, val = f
            key, field_action = _split(key)
            if key == 'or_':
                rv.append({'or':_process_filters(val.items())})
            elif field_action is None:
                rv.append({'term': {key: val}})
            elif field_action == 'in':
                rv.append({'in': {key: val}})
            elif field_action in ('gt', 'gte', 'lt', 'lte'):
                rv.append({'range': {key: {field_action: val}}})
            else:
                raise InvalidFieldActionError(
                    '%s is not a valid field action' % field_action)
    return rv


def _process_facets(facets, flags):
    rv = {}
    for fieldname in facets:
        facet_type = {'terms': {'field': fieldname}}
        if flags.get('global_'):
            facet_type['global'] = flags['global_']
        elif flags.get('filtered'):
            # Note: This is an indicator that the facet_filter should
            # get filled in later when we know all the filters.
            facet_type['facet_filter'] = None

        rv[fieldname] = facet_type
    return rv


class F(object):
    """
    Filter objects.
    """
    def __init__(self, **filters):
        """Creates an F

        :raises InvalidFieldActionError: if the field action is not
            valid

        """
        if filters:
            items = _process_filters(filters.items())
            if len(items) > 1:
                self.filters = {'and': items}
            else:
                self.filters = items[0]
        else:
            self.filters = {}

    def _combine(self, other, conn='and'):
        """
        OR and AND will create a new F, with the filters from both F
        objects combined with the connector `conn`.
        """
        f = F()
        if not self.filters:
            f.filters = other.filters
        elif not other.filters:
            f.filters = self.filters
        elif conn in self.filters:
            f.filters = self.filters
            f.filters[conn].append(other.filters)
        elif conn in other.filters:
            f.filters = other.filters
            f.filters[conn].append(self.filters)
        else:
            f.filters = {conn: [self.filters, other.filters]}
        return f

    def __or__(self, other):
        return self._combine(other, 'or')

    def __and__(self, other):
        return self._combine(other, 'and')

    def __invert__(self):
        f = F()
        if (len(self.filters) < 2 and
           'not' in self.filters and 'filter' in self.filters['not']):
            f.filters = self.filters['not']['filter']
        else:
            f.filters = {'not': {'filter': self.filters}}
        return f


# Number of results to show before truncating when repr(S)
REPR_OUTPUT_SIZE = 20


def _boosted_value(name, action, key, value, boost):
    """Boost a value if we should in _process_queries"""
    if boost is not None:
        # Note: Most queries use 'value' for the key name except Text
        # queries which use 'query'. So we have to do some switcheroo
        # for that.
        return {
            name: {
                'boost': boost,
                'query' if action == 'text' else 'value': value}}
    return {name: value}


# Maps ElasticUtils field actions to their ElasticSearch query names.
ACTION_MAP = {
    None: 'term',  # Default to term
    'in': 'in',
    'term': 'term',
    'startswith': 'prefix',  # Backwards compatability
    'prefix': 'prefix',
    'text': 'text',
    'text_phrase': 'text_phrase',
    'fuzzy': 'fuzzy'}


class S(object):
    """
    Represents a lazy ElasticSearch lookup, with a similar api to
    Django's QuerySet.
    """
    def __init__(self, type_=None):
        """Create and return an S.

        :arg type_: class; the model that this S is based on

        """
        self.type = type_
        self.steps = []
        self.start = 0
        self.stop = None
        self.as_list = self.as_dict = False
        self.field_boosts = {}
        self._results_cache = None

    def __repr__(self):
        data = list(self)[:REPR_OUTPUT_SIZE + 1]
        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)

    def _clone(self, next_step=None):
        new = self.__class__(self.type)
        new.steps = list(self.steps)
        if next_step:
            new.steps.append(next_step)
        new.start = self.start
        new.stop = self.stop
        new.field_boosts = self.field_boosts.copy()
        return new

    def es(self, **settings):
        """Return a new S with specified ES settings.

        This allows you to configure the ES that gets used to execute
        the search.

        :arg settings: the settings you'd use to build the ES---same
            as what you'd pass to :fun:`get_es`.

        """
        return self._clone(next_step=('es', settings))

    def es_builder(self, builder_function):
        """Return a new S with specified ES builder.

        When you do something with an S that causes it to execute a
        search, then it will call the specified builder function with
        the S instance. The builder function will return an ES object
        that the S will use to execute the search with.

        :arg builder_function: function; takes an S instance and returns
            an ES

        This is handy for caching ES instances. For example, you could
        create a builder that caches ES instances thread-local::

            from threading import local
            _local = local()

            def thread_local_builder(searcher):
                if not hasattr(_local, 'es'):
                    _local.es = get_es()
                return _local.es

            searcher = S.es_builder(thread_local_builder)

        This is also handy for building ES instances with
        configuration defined in a config file.

        """
        return self._clone(next_step=('es_builder', builder_function))

    def indexes(self, *indexes):
        """
        Return a new S instance that will search specified indexes.
        """
        return self._clone(next_step=('indexes', indexes))

    def doctypes(self, *doctypes):
        """
        Return a new S instance that will search specified doctypes.

        .. Note::

           ElasticSearch calls these "mapping types". It's the name
           associated with a mapping.
        """
        return self._clone(next_step=('doctypes', doctypes))

    def explain(self, value=True):
        """
        Return a new S instance with explain set.
        """
        return self._clone(next_step=('explain', value))

    def values_list(self, *fields):
        """
        Return a new S instance that returns ListSearchResults.
        """
        return self._clone(next_step=('values_list', fields))

    def values_dict(self, *fields):
        """
        Return a new S instance that returns DictSearchResults.
        """
        return self._clone(next_step=('values_dict', fields))

    def order_by(self, *fields):
        """
        Return a new S instance with the ordering changed.
        """
        return self._clone(next_step=('order_by', fields))

    def query(self, **kw):
        """
        Return a new S instance with query args combined with existing
        set.
        """
        return self._clone(next_step=('query', kw.items()))

    def filter(self, *filters, **kw):
        """
        Return a new S instance with filter args combined with
        existing set.
        """
        return self._clone(next_step=('filter', list(filters) + kw.items()))

    def boost(self, **kw):
        """
        Return a new S instance with field boosts.
        """
        new = self._clone()
        new.field_boosts.update(kw)
        return new

    def demote(self, amount_, **kw):
        """
        Returns a new S instance with boosting query and demotion.
        """
        return self._clone(next_step=('demote', (amount_, kw)))

    def facet(self, *args, **kw):
        """
        Return a new S instance with facet args combined with existing
        set.
        """
        return self._clone(next_step=('facet', (args, kw)))

    def facet_raw(self, **kw):
        """
        Return a new S instance with raw facet args combined with
        existing set.
        """
        return self._clone(next_step=('facet_raw', kw.items()))

    def highlight(self, *fields, **kwargs):
        """Set highlight/excerpting with specified options.

        This highlight will override previous highlights.

        This won't let you clear it--we'd need to write a
        ``clear_highlight()``.

        :arg fields: The list of fields to highlight. If the field is
            None, then the highlight is cleared.

        Additional keyword options:

        * ``pre_tags`` -- List of tags before highlighted portion
        * ``post_tags`` -- List of tags after highlighted portion

        See ElasticSearch highlight:

        http://www.elasticsearch.org/guide/reference/api/search/highlighting.html

        """
        # TODO: Implement `limit` kwarg if useful.
        # TODO: Once oedipus is no longer needed in SUMO, support ranked lists
        # of before_match and after_match tags. ES can highlight more
        # significant stuff brighter.
        return self._clone(next_step=('highlight', (fields, kwargs)))

    def extra(self, **kw):
        """
        Return a new S instance with extra args combined with existing
        set.
        """
        new = self._clone()
        actions = 'values_list values_dict order_by query filter facet'.split()
        for key, vals in kw.items():
            assert key in actions
            if hasattr(vals, 'items'):
                new.steps.append((key, vals.items()))
            else:
                new.steps.append((key, vals))
        return new

    def count(self):
        """
        Return the number of hits for the search as an integer.
        """
        if self._results_cache:
            return self._results_cache.count
        else:
            return self[:0].raw()['hits']['total']

    def __len__(self):
        return len(self._do_search())

    def __getitem__(self, k):
        new = self._clone()
        # TODO: validate numbers and ranges
        if isinstance(k, slice):
            new.start, new.stop = k.start or 0, k.stop
            return new
        else:
            new.start, new.stop = k, k + 1
            return list(new)[0]

    def _build_query(self):
        """
        Loop self.steps to build the query format that will be sent to
        ElasticSearch, and return it as a dict.
        """
        filters = []
        queries = []
        sort = []
        fields = set(['id'])
        facets = {}
        facets_raw = {}
        demote = None
        highlight_fields = set()
        highlight_options = {}
        explain = False
        as_list = as_dict = False
        for action, value in self.steps:
            if action == 'order_by':
                sort = []
                for key in value:
                    if key.startswith('-'):
                        sort.append({key[1:]: 'desc'})
                    else:
                        sort.append(key)
            elif action == 'values_list':
                fields |= set(value)
                as_list, as_dict = True, False
            elif action == 'values_dict':
                if not value:
                    fields = set()
                else:
                    fields |= set(value)
                as_list, as_dict = False, True
            elif action == 'explain':
                explain = value
            elif action == 'query':
                queries.extend(self._process_queries(value))
            elif action == 'demote':
                demote = (value[0], self._process_queries(value[1]))
            elif action == 'filter':
                filters.extend(_process_filters(value))
            elif action == 'facet':
                # value here is a (args, kwargs) tuple
                facets.update(_process_facets(*value))
            elif action == 'facet_raw':
                facets_raw.update(dict(value))
            elif action == 'highlight':
                if value[0] == (None,):
                    highlight_fields = set()
                else:
                    highlight_fields |= set(value[0])
                highlight_options.update(value[1])
            elif action in ('es_builder', 'es', 'indexes', 'doctypes', 'boost'):
                # Ignore these--we use these elsewhere, but want to
                # make sure lack of handling it here doesn't throw an
                # error.
                pass
            else:
                raise NotImplementedError(action)

        qs = {}
        if len(filters) > 1:
            qs['filter'] = {'and': filters}
        elif filters:
            qs['filter'] = filters[0]

        if len(queries) > 1:
            qs['query'] = {'bool': {'must': queries}}
        elif queries:
            qs['query'] = queries[0]

        if demote is not None:
            qs['query'] = {
                'boosting': {
                    'positive': qs['query'],
                    'negative': demote[1],
                    'negative_boost': demote[0]
                    }
                }

        if fields:
            qs['fields'] = list(fields)

        if facets:
            qs['facets'] = facets
            # Hunt for `facet_filter` shells and update those. We use
            # None as a shell, so if it's explicitly set to None, then
            # we update it.
            for facet in facets.values():
                if facet.get('facet_filter', 1) is None:
                    facet['facet_filter'] = qs['filter']

        if facets_raw:
            qs.setdefault('facets', {}).update(facets_raw)

        if sort:
            qs['sort'] = sort
        if self.start:
            qs['from'] = self.start
        if self.stop is not None:
            qs['size'] = self.stop - self.start

        if highlight_fields:
            qs['highlight'] = self._build_highlight(
                highlight_fields, highlight_options)

        if explain:
            qs['explain'] = True

        self.fields, self.as_list, self.as_dict = fields, as_list, as_dict
        return qs

    def _build_highlight(self, fields, options):
        """Return the portion of the query that controls highlighting."""
        ret = {'fields': dict((f, {}) for f in fields),
               'order': 'score'}
        ret.update(options)
        return ret

    def _process_queries(self, value):
        rv = []
        value = dict(value)
        or_ = value.pop('or_', [])
        for key, val in value.items():
            field_name, field_action = _split(key)

            # Boost by name__action overrides boost by name.
            boost = self.field_boosts.get(key)
            if boost is None:
                boost = self.field_boosts.get(field_name)

            if field_action in ACTION_MAP:
                rv.append(
                    {ACTION_MAP[field_action]: _boosted_value(
                            field_name, field_action, key, val, boost)})

            elif field_action == 'query_string':
                # query_string has different syntax, so it's handled
                # differently.
                #
                # Note: query_string queries are not boosted with
                # .boost()---they're boosted in the query text itself.
                rv.append(
                    {'query_string':
                         {'default_field': field_name,
                          'query': val}})

            elif field_action in ('gt', 'gte', 'lt', 'lte'):
                # Ranges are special and have a different syntax, so
                # we handle them separately.
                rv.append(
                    {'range': {field_name: _boosted_value(
                                field_name, field_action, key, val, boost)}})

            else:
                raise InvalidFieldActionError(
                    '%s is not a valid field action' % field_action)

        if or_:
            rv.append({'bool': {'should': self._process_queries(or_.items())}})
        return rv

    def _do_search(self):
        """
        Perform the search, then convert that raw format into a
        SearchResults instance and return it.
        """
        if not self._results_cache:
            hits = self.raw()
            if self.as_list:
                ResultClass = ListSearchResults
            elif self.as_dict or self.type is None:
                ResultClass = DictSearchResults
            else:
                ResultClass = ObjectSearchResults
            self._results_cache = ResultClass(self.type, hits, self.fields)
        return self._results_cache

    def get_es(self, default_builder=get_es):
        # The last one overrides earlier ones.
        for action, value in reversed(self.steps):
            if action == 'es_builder':
                # es_builder overrides es
                return value(self)
            elif action == 'es':
                return get_es(**value)

        return default_builder()

    def get_indexes(self, default_indexes=DEFAULT_INDEXES):
        for action, value in reversed(self.steps):
            if action == 'indexes':
                return value

        return default_indexes

    def get_doctypes(self, default_doctypes=DEFAULT_DOCTYPES):
        for action, value in reversed(self.steps):
            if action == 'doctypes':
                return value
        return default_doctypes

    def raw(self):
        """
        Build query and passes to ElasticSearch, then returns the raw
        format returned.
        """
        qs = self._build_query()
        es = self.get_es()
        try:
            hits = es.search(qs, self.get_indexes(), self.get_doctypes())
        except Exception:
            log.error(qs)
            raise
        log.debug('[%s] %s' % (hits['took'], qs))
        if hasattr(_local, '_es_queries'):
            _local._es_queries.append({
                'query': qs,
                'time': hits['took']
            })
        return hits

    def __iter__(self):
        return iter(self._do_search())

    def _raw_facets(self):
        return self._do_search().results.get('facets', {})

    def facet_counts(self):
        facets = {}
        for key, val in self._raw_facets().items():
            if val['_type'] == 'terms':
                facets[key] = [v for v in val['terms']]
            elif val['_type'] == 'range':
                facets[key] = [v for v in val['ranges']]
        return facets


class SearchResults(object):
    def __init__(self, type, results, fields):
        self.type = type
        self.took = results['took']
        self.count = results['hits']['total']
        self.results = results
        self.fields = fields
        self.set_objects(results['hits']['hits'])

    def set_objects(self, hits):
        raise NotImplementedError()

    def __iter__(self):
        return iter(self.objects)

    def __len__(self):
        return len(self.objects)


class DictResult(dict):
    pass


class TupleResult(tuple):
    pass


class DictSearchResults(SearchResults):
    def set_objects(self, hits):
        key = 'fields' if self.fields else '_source'
        self.objects = [_decorate_with_metadata(DictResult(r[key]), r)
                        for r in hits]


class ListSearchResults(SearchResults):
    def set_objects(self, hits):
        if self.fields:
            getter = itemgetter(*self.fields)
            objs = [(getter(r['fields']), r) for r in hits]

            # itemgetter returns an item--not a tuple of one item--if
            # there is only one thing in self.fields. Since we want
            # this to always return a list of tuples, we need to fix
            # that case here.
            if len(self.fields) == 1:
                objs = [((obj,), r) for obj, r in objs]
        else:
            objs = [(r['_source'].values(), r) for r in hits]
        self.objects = [_decorate_with_metadata(TupleResult(obj), r)
                        for obj, r in objs]


class ObjectSearchResults(SearchResults):
    def set_objects(self, hits):
        self.ids = [int(r['_id']) for r in hits]
        self.objects = self.type.objects.filter(id__in=self.ids)

    def __iter__(self):
        objs = dict((obj.id, obj) for obj in self.objects)
        return (_decorate_with_metadata(objs[id], r)
                for id, r in
                izip(self.ids, self.results['hits']['hits'])
                if id in objs)


def _decorate_with_metadata(obj, hit):
    """Return obj decorated with hit-scope metadata."""
    # The search result score
    obj._score = hit.get('_score')
    # The document type
    obj._type = hit.get('_type')
    # Explanation structure
    obj._explanation = hit.get('_explanation', {})
    # Highlight bits
    obj._highlight = hit.get('highlight', {})
    return obj


import threading
from django.conf import settings

if settings.DEBUG:
    from django.core import signals

    _local = threading.local()
    _local._es_queries = []

    # A DEBUG only ES request storage with request_started signal to clear.
    def reset_search_queries(**kwargs):
        _local._es_queries = []

    signals.request_started.connect(reset_search_queries)
