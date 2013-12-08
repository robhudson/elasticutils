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

    attrs = ('boost', 'include_in_all', 'index', 'null_value', 'store')
    bool_casts = ('include_in_all',)
    float_casts = ('boost',)
    int_casts = ()

    # Used to maintain the order of fields as defined in the class.
    _creation_order = 0

    def __init__(self, *args, **kwargs):
        self.index_fieldname = kwargs.pop('index_fieldname', None)
        self.is_multivalued = kwargs.pop('is_multivalued', None)

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
                if attr in self.bool_casts:
                    if not val or val == 'false':
                        f[attr] = False
                    else:
                        f[attr] = True
                elif attr in self.float_casts:
                    f[attr] = float(val)
                elif attr in self.int_casts:
                    f[attr] = int(val)
                else:
                    f[attr] = str(val)

        return f


class StringField(SearchField):
    field_type = 'string'
    attrs = SearchField.attrs + (
        'analyzer', 'ignore_above',
        'index_analyzer', 'index_options', 'omit_norms',
        'position_offset_gap', 'search_analyzer', 'term_vector')
    bool_casts = SearchField.bool_casts + ('omit_norms',)
    int_casts = SearchField.int_casts + ('position_offset_gap',)

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


class NumberFieldBase(SearchField):
    attrs = SearchField.attrs + ('ignore_malformed', 'precision_step')
    bool_casts = SearchField.bool_casts + ('ignore_malformed',)
    int_casts = SearchField.int_casts + ('precision_step',)


class IntegerField(NumberFieldBase):
    field_type = 'integer'
    int_casts = NumberFieldBase.int_casts + ('null_value',)

    def __init__(self, type='integer', *args, **kwargs):
        if type in ('byte', 'short', 'integer', 'long'):
            self.field_type = type
        for attr in self.attrs:
            setattr(self, attr, kwargs.pop(attr, None))
        super(IntegerField, self).__init__(*args, **kwargs)

    def prepare(self, value):
        return self.convert(super(IntegerField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return int(value)


class FloatField(NumberFieldBase):
    field_type = 'float'
    float_casts = NumberFieldBase.float_casts + ('null_value',)

    def __init__(self, type='float', *args, **kwargs):
        if type in ('float', 'double'):
            self.field_type = type
        for attr in self.attrs:
            setattr(self, attr, kwargs.pop(attr, None))
        super(FloatField, self).__init__(*args, **kwargs)

    def prepare(self, value):
        return self.convert(super(FloatField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return float(value)


class DecimalField(StringField):

    def __init__(self, *args, **kwargs):
        for attr in self.attrs:
            setattr(self, attr, kwargs.pop(attr, None))
        super(DecimalField, self).__init__(*args, **kwargs)

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
    bool_casts = SearchField.bool_casts + ('null_value',)

    def __init__(self, *args, **kwargs):
        for attr in self.attrs:
            setattr(self, attr, kwargs.pop(attr, None))
        super(BooleanField, self).__init__(*args, **kwargs)

    def prepare(self, value):
        return self.convert(super(BooleanField, self).prepare(value))

    def convert(self, value):
        if value is None:
            return None

        return bool(value)


class DateFieldBase(SearchField):
    attrs = SearchField.attrs + ('format', 'ignore_malformed',
                                 'precision_step')
    bool_casts = SearchField.bool_casts + ('ignore_malformed',)
    int_casts = SearchField.int_casts + ('precision_step',)


class DateField(DateFieldBase):
    field_type = 'date'

    def __init__(self, *args, **kwargs):
        for attr in self.attrs:
            setattr(self, attr, kwargs.pop(attr, None))
        super(DateField, self).__init__(*args, **kwargs)

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
    attrs = ()
    bool_casts = ()
    float_casts = ()
    int_casts = ()

    def prepare(self, value):
        if value is None:
            return None

        return base64.b64encode(value)

    def convert(self, value):
        if value is None:
            return None

        return base64.b64decode(value)
