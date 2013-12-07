import base64
import datetime
import re
from decimal import Decimal

from .exceptions import SearchFieldError


DATE_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}).*?$')
DATETIME_REGEX = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'
                            '(T|\s+)(?P<hour>\d{2}):(?P<minute>\d{2}):'
                            '(?P<second>\d{2}).*?$')


class SearchField(object):

    field_type = None

    # Used to maintain the order of fields as defined in the class.
    _creation_order = 0

    def __init__(self, index_fieldname=None, is_multivalued=False):
        self.index_fieldname = index_fieldname
        self.is_multivalued = is_multivalued

        # Store this fields order.
        self._creation_order = SearchField._creation_order
        # Increment order number for future fields.
        SearchField._creation_order += 1

    def prepare(self, value):
        """
        Handles conversion between the value sent to Elasticsearch and the type
        of the field.

        Extending classes should override this method.
        """
        return value

    def convert(self, value):
        """
        Handles conversion between the data received from Elasticsearch and the
        type of the field.

        Extending classes should override this method.
        """
        return value

    def get_definition(self):
        """
        Returns the resprentation for this field's definition in the mapping.
        """
        return {'type': self.field_type}


class StringField(SearchField):
    field_type = 'string'
    attrs = ('analyzer', 'boost', 'ignore_above', 'include_in_all', 'index',
             'index_analyzer', 'index_options', 'null_value', 'omit_norms',
             'position_offset_gap', 'search_analyzer', 'store', 'term_vector')
    attr_casts = {
        'float': ['boost'],
        'int': ['position_offset_gap'],
        'bool': ['omit_norms', 'include_in_all'],
    }

    def __init__(self, *args, **kwargs):
        for attr in self.attrs:
            setattr(self, attr, kwargs.pop(attr, None))

        super(StringField, self).__init__(*args, **kwargs)

    def prepare(self, value):
        return self.convert(super(StringField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return unicode(value)

    def get_definition(self):
        f = super(StringField, self).get_definition()

        for attr in self.attrs:
            val = getattr(self, attr, None)
            if val is not None:
                if attr in self.attr_casts['bool']:
                    if not val or val == 'false':
                        f[attr] = False
                    else:
                        f[attr] = True
                elif attr in self.attr_casts['float']:
                    f[attr] = float(val)
                elif attr in self.attr_casts['int']:
                    f[attr] = int(val)
                else:
                    f[attr] = val

        return f


# TODO: Support all attributes for number types:
# http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-core-types.html#number
class IntegerField(SearchField):
    field_type = 'integer'

    def __init__(self, type='integer', *args, **kwargs):
        if type in ('byte', 'short', 'integer', 'long'):
            self.field_type = type
        super(IntegerField, self).__init__(*args, **kwargs)

    def prepare(self, value):
        return self.convert(super(IntegerField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return int(value)


class FloatField(SearchField):
    field_type = 'float'

    def __init__(self, type='float', *args, **kwargs):
        if type in ('float', 'double'):
            self.field_type = type
        super(FloatField, self).__init__(*args, **kwargs)

    def prepare(self, value):
        return self.convert(super(FloatField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return float(value)


class DecimalField(SearchField):
    field_type = 'string'

    def prepare(self, value):
        return self.convert(super(DecimalField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return Decimal(str(value))


# TODO: Support all attributes for boolean types:
# http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-core-types.html#boolean
class BooleanField(SearchField):
    field_type = 'boolean'

    def prepare(self, value):
        return self.convert(super(BooleanField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return bool(value)


# TODO: Support all attributes for date types:
# http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-core-types.html#date
class DateField(SearchField):
    field_type = 'date'

    def convert(self, value):
        if value is None:
            return None

        if isinstance(value, basestring):
            match = DATE_REGEX.search(value)

            if match:
                data = match.groupdict()
                return datetime.date(
                    int(data['year']), int(data['month']), int(data['day']))
            else:
                raise SearchFieldError(
                    "Date provided to '%s' field doesn't appear to be a valid "
                    "date string: '%s'" % (self.instance_name, value))

        return value


class DateTimeField(SearchField):
    field_type = 'datetime'

    def convert(self, value):
        if value is None:
            return None

        if isinstance(value, basestring):
            match = DATETIME_REGEX.search(value)

            if match:
                data = match.groupdict()
                return datetime.datetime(
                    int(data['year']), int(data['month']), int(data['day']),
                    int(data['hour']), int(data['minute']),
                    int(data['second']))
            else:
                raise SearchFieldError(
                    "Datetime provided to '%s' field doesn't appear to be a "
                    "valid datetime string: '%s'" % (
                        self.instance_name, value))

        return value


class BinaryField(SearchField):
    field_type = 'binary'

    def prepare(self, value):
        if value is None:
            return None

        return base64.b64encode(value)

    def convert(self, value):
        if value is None:
            return None

        return base64.b64decode(value)


# TODO: Not sure we need this actually. Multivalued field types can be their
# base class (e.g. IntegerField(multivalue=True) so Python knows how to return
# data.
class MultiValueField(SearchField):
    field_type = 'string'

    def __init__(self, **kwargs):
        super(MultiValueField, self).__init__(**kwargs)
        self.is_multivalued = True

    def prepare(self, value):
        return self.convert(super(MultiValueField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return list(value)
