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
        f = {'type': self.field_type}

        for attr in self.attrs:
            val = getattr(self, attr, None)
            if val is not None:
                f[attr] = val

        return f


class StringField(SearchField):
    field_type = 'string'

    def prepare(self, value):
        return self.convert(super(StringField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return unicode(value)


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


class DecimalField(StringField):

    def prepare(self, value):
        if value is None:
            return None

        return str(value)

    def convert(self, value):
        if value is None:
            return None

        return Decimal(str(value))


class BooleanField(SearchField):
    field_type = 'boolean'

    def prepare(self, value):
        return self.convert(super(BooleanField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return bool(value)


class DateField(SearchField):
    field_type = 'date'

    def prepare(self, value):
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.isoformat()

        return value

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


class DateTimeField(DateField):

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
