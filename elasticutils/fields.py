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

    # TODO: Determine more attributes that need setting.
    def __init__(self, analyzer=None, index_fieldname=None, boost=None,
                 is_multivalued=False, analyzed=True):
        self.analyzer = analyzer
        self.index_fieldname = index_fieldname
        self.boost = boost
        self.is_multivalued = is_multivalued
        self.analyzed = analyzed

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


# TODO: Support all attributes for string types:
# http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/mapping-core-types.html#string
class StringField(SearchField):
    field_type = 'string'

    def prepare(self, value):
        return self.convert(super(StringField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return unicode(value)


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
