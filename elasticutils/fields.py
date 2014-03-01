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
    attrs = []

    # Used to maintain the order of fields as defined in the class.
    _creation_order = 0

    def __init__(self, *args, **kwargs):
        # These are special.
        for attr in ('index_fieldname', 'is_multivalue'):
            setattr(self, attr, kwargs.pop(attr, None))

        # Set all kwargs on self for later access.
        for attr in kwargs.keys():
            self.attrs.append(attr)
            setattr(self, attr, kwargs.pop(attr, None))

        # Store this fields order.
        self._creation_order = SearchField._creation_order
        # Increment order number for future fields.
        SearchField._creation_order += 1

    def to_es(self, value):
        """
        Converts a Python value to an Elasticsearch value.

        Extending classes should override this method.
        """
        return value

    def to_python(self, value):
        """
        Converts an Elasticsearch value to a Python value.

        Extending classes should override this method.
        """
        return value

    def get_definition(self):
        """
        Returns the resprentation for this field's definition in the mapping.
        """
        f = {'type': self.field_type}

        for attr in self.attrs:
            val = getattr(self, attr, None)
            if val is not None:
                f[attr] = val

        return f


class StringField(SearchField):
    field_type = 'string'

    def to_es(self, value):
        if value is None:
            return None

        return unicode(value)

    def to_python(self, value):
        if value is None:
            return None

        return unicode(value)


class IntegerField(SearchField):
    field_type = 'integer'

    def __init__(self, type='integer', *args, **kwargs):
        if type in ('byte', 'short', 'integer', 'long'):
            self.field_type = type
        super(IntegerField, self).__init__(*args, **kwargs)

    def to_es(self, value):
        if value is None:
            return None

        return int(value)

    def to_python(self, value):
        if value is None:
            return None

        return int(value)


class FloatField(SearchField):
    field_type = 'float'

    def __init__(self, type='float', *args, **kwargs):
        if type in ('float', 'double'):
            self.field_type = type
        super(FloatField, self).__init__(*args, **kwargs)

    def to_es(self, value):
        if value is None:
            return None

        return float(value)

    def to_python(self, value):
        if value is None:
            return None

        return float(value)


class DecimalField(StringField):

    def to_es(self, value):
        if value is None:
            return None

        return str(float(value))

    def to_python(self, value):
        if value is None:
            return None

        return Decimal(str(value))


class BooleanField(SearchField):
    field_type = 'boolean'

    def to_es(self, value):
        if value is None:
            return None

        return bool(value)

    def to_python(self, value):
        if value is None:
            return None

        return bool(value)


class DateField(SearchField):
    field_type = 'date'

    def to_es(self, value):
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.isoformat()

        return value

    def to_python(self, value):
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


class DateTimeField(DateField):

    def to_python(self, value):
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

    def to_es(self, value):
        if value is None:
            return None

        return base64.b64encode(value)

    def to_python(self, value):
        if value is None:
            return None

        return base64.b64decode(value)
