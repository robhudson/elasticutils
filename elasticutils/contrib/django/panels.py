import json

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from debug_toolbar.panels import DebugPanel


from elasticutils import _local


class ElasticutilsDebugPanel(DebugPanel):
    """
    Panel that displays information about the elasticsearch queries that were
    run while processing the request.
    """
    name = 'Elasticsearch'
    has_content = True

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self._search_time = 0
        self._queries = []

    def nav_title(self):
        return _('Elasticsearch')

    def nav_subtitle(self):
        if hasattr(_local, '_es_queries'):
            self._queries = _local._es_queries[:]
        else:
            self._queries = []

        for q in self._queries:
            q['query'] = json.dumps(q, sort_keys=True)
            self._search_time += q['time']
        num_queries = len(self._queries)

        return "%d %s in %.2fms" % (
            num_queries,
            (num_queries == 1) and 'query' or 'queries',
            self._search_time
        )

    def title(self):
        return _('Search Queries')

    def url(self):
        return ''

    def content(self):
        width_ratio_tally = 0

        for query in self._queries:
            try:
                query['width_ratio'] = (float(query['time']) / self._search_time) * 100
            except ZeroDivisionError:
                query['width_ratio'] = 0

            query['start_offset'] = width_ratio_tally
            width_ratio_tally += query['width_ratio']

        context = self.context.copy()
        context.update({
            'queries': self._queries,
            'sql_time': self._search_time,
        })

        return render_to_string('panels/elasticsearch.html', context)
