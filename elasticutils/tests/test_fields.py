import base64
import datetime
from decimal import Decimal
from unittest import TestCase

from nose.tools import eq_

from elasticutils import fields


class TestStringField(TestCase):

    def test_type(self):
        eq_(fields.StringField().field_type, 'string')

    def test_prepare(self):
        eq_(fields.StringField().prepare('test'), 'test')

    def test_convert(self):
        eq_(fields.StringField().convert(None), None)
        eq_(fields.StringField().convert('test'), 'test')

    def test_index(self):
        field = fields.StringField(index='not_analyzed')
        eq_(field.get_definition()['index'], 'not_analyzed')

    def test_store(self):
        field = fields.StringField(store='yes')
        eq_(field.get_definition()['store'], 'yes')

    def test_term_vector(self):
        field = fields.StringField(term_vector='with_offsets')
        eq_(field.get_definition()['term_vector'], 'with_offsets')

    def test_boost(self):
        field = fields.StringField(boost=2.5)
        eq_(field.get_definition()['boost'], 2.5)
        field = fields.StringField(boost='2.5')
        eq_(field.get_definition()['boost'], 2.5)

    def test_null_value(self):
        field = fields.StringField(null_value='na')
        eq_(field.get_definition()['null_value'], 'na')

    def test_boolean_attributes(self):
        for attr in ('omit_norms', 'include_in_all'):
            # Test truthiness.
            field = fields.StringField(**{attr: True})
            eq_(field.get_definition()[attr], True)
            field = fields.StringField(**{attr: 'true'})
            eq_(field.get_definition()[attr], True)
            # Test falsiness.
            field = fields.StringField(**{attr: False})
            eq_(field.get_definition()[attr], False)
            field = fields.StringField(**{attr: ''})
            eq_(field.get_definition()[attr], False)

    def test_index_options(self):
        field = fields.StringField(index_options='positions')
        eq_(field.get_definition()['index_options'], 'positions')

    def test_analyzer(self):
        field = fields.StringField(analyzer='snowball')
        eq_(field.get_definition()['analyzer'], 'snowball')

    def test_index_analyzer(self):
        field = fields.StringField(index_analyzer='snowball')
        eq_(field.get_definition()['index_analyzer'], 'snowball')

    def test_search_analyzer(self):
        field = fields.StringField(search_analyzer='snowball')
        eq_(field.get_definition()['search_analyzer'], 'snowball')

    def test_ignore_above(self):
        field = fields.StringField(ignore_above='1024')
        eq_(field.get_definition()['ignore_above'], '1024')

    def test_position_offset_gap(self):
        field = fields.StringField(position_offset_gap=2)
        eq_(field.get_definition()['position_offset_gap'], 2)
        field = fields.StringField(position_offset_gap='2')
        eq_(field.get_definition()['position_offset_gap'], 2)


class TestIntegerField(TestCase):

    def test_type(self):
        eq_(fields.IntegerField().field_type, 'integer')
        eq_(fields.IntegerField(type='byte').field_type, 'byte')
        eq_(fields.IntegerField(type='short').field_type, 'short')
        eq_(fields.IntegerField(type='long').field_type, 'long')
        eq_(fields.IntegerField(type='foo').field_type, 'integer')

    def test_prepare(self):
        eq_(fields.IntegerField().prepare(100), 100)

    def test_convert(self):
        eq_(fields.IntegerField().convert(None), None)
        eq_(fields.IntegerField().convert(100), 100)

    def test_index(self):
        field = fields.IntegerField(index='no')
        eq_(field.get_definition()['index'], 'no')

    def test_store(self):
        field = fields.IntegerField(store='yes')
        eq_(field.get_definition()['store'], 'yes')

    def test_precision_step(self):
        field = fields.IntegerField(precision_step=4)
        eq_(field.get_definition()['precision_step'], 4)

    def test_boost(self):
        field = fields.IntegerField(boost=2.5)
        eq_(field.get_definition()['boost'], 2.5)
        field = fields.IntegerField(boost='2.5')
        eq_(field.get_definition()['boost'], 2.5)

    def test_null_value(self):
        field = fields.IntegerField(null_value=1)
        eq_(field.get_definition()['null_value'], 1)

    def test_boolean_attributes(self):
        for attr in ('ignore_malformed', 'include_in_all'):
            # Test truthiness.
            field = fields.IntegerField(**{attr: True})
            eq_(field.get_definition()[attr], True)
            field = fields.IntegerField(**{attr: 'true'})
            eq_(field.get_definition()[attr], True)
            # Test falsiness.
            field = fields.IntegerField(**{attr: False})
            eq_(field.get_definition()[attr], False)
            field = fields.IntegerField(**{attr: ''})
            eq_(field.get_definition()[attr], False)


class TestFloatField(TestCase):

    def test_type(self):
        eq_(fields.FloatField().field_type, 'float')
        eq_(fields.FloatField(type='double').field_type, 'double')
        eq_(fields.FloatField(type='foo').field_type, 'float')

    def test_prepare(self):
        eq_(fields.FloatField().prepare(100), 100.0)

    def test_convert(self):
        eq_(fields.FloatField().convert(None), None)
        eq_(fields.FloatField().convert(100), 100.0)

    def test_index(self):
        field = fields.FloatField(index='no')
        eq_(field.get_definition()['index'], 'no')

    def test_store(self):
        field = fields.FloatField(store='yes')
        eq_(field.get_definition()['store'], 'yes')

    def test_precision_step(self):
        field = fields.FloatField(precision_step=4)
        eq_(field.get_definition()['precision_step'], 4)

    def test_boost(self):
        field = fields.FloatField(boost=2.5)
        eq_(field.get_definition()['boost'], 2.5)
        field = fields.FloatField(boost='2.5')
        eq_(field.get_definition()['boost'], 2.5)

    def test_null_value(self):
        field = fields.FloatField(null_value=1.0)
        eq_(field.get_definition()['null_value'], 1.0)

    def test_boolean_attributes(self):
        for attr in ('ignore_malformed', 'include_in_all'):
            # Test truthiness.
            field = fields.FloatField(**{attr: True})
            eq_(field.get_definition()[attr], True)
            field = fields.FloatField(**{attr: 'true'})
            eq_(field.get_definition()[attr], True)
            # Test falsiness.
            field = fields.FloatField(**{attr: False})
            eq_(field.get_definition()[attr], False)
            field = fields.FloatField(**{attr: ''})
            eq_(field.get_definition()[attr], False)


class TestDecimalField(TestCase):
    """DecimalField subclasses StringField, so we just test a few things."""

    def test_type(self):
        eq_(fields.DecimalField().field_type, 'string')

    def test_prepare(self):
        eq_(fields.DecimalField().prepare(Decimal('100.0')), '100.0')

    def test_convert(self):
        eq_(fields.DecimalField().convert(None), None)
        eq_(fields.DecimalField().convert('100.0'), Decimal('100.0'))


class TestBooleanField(TestCase):

    def test_type(self):
        eq_(fields.BooleanField().field_type, 'boolean')

    def test_prepare(self):
        eq_(fields.BooleanField().prepare(True), True)
        eq_(fields.BooleanField().prepare(False), False)

    def test_convert(self):
        eq_(fields.BooleanField().convert(None), None)
        eq_(fields.BooleanField().convert(True), True)
        eq_(fields.BooleanField().convert(False), False)

    def test_index(self):
        field = fields.BooleanField(index='no')
        eq_(field.get_definition()['index'], 'no')

    def test_store(self):
        field = fields.BooleanField(store='yes')
        eq_(field.get_definition()['store'], 'yes')

    def test_boost(self):
        field = fields.BooleanField(boost=2.5)
        eq_(field.get_definition()['boost'], 2.5)
        field = fields.BooleanField(boost='2.5')
        eq_(field.get_definition()['boost'], 2.5)

    def test_null_value(self):
        field = fields.BooleanField(null_value=True)
        eq_(field.get_definition()['null_value'], True)

    def test_boolean_attributes(self):
        # Test truthiness.
        field = fields.BooleanField(include_in_all=True)
        eq_(field.get_definition()['include_in_all'], True)
        field = fields.BooleanField(include_in_all='true')
        eq_(field.get_definition()['include_in_all'], True)
        # Test falsiness.
        field = fields.BooleanField(include_in_all=False)
        eq_(field.get_definition()['include_in_all'], False)
        field = fields.BooleanField(include_in_all='')
        eq_(field.get_definition()['include_in_all'], False)


class TestDateField(TestCase):

    def test_type(self):
        eq_(fields.DateField().field_type, 'date')

    def test_prepare(self):
        eq_(fields.DateField().prepare(datetime.date(2013, 11, 22)),
            '2013-11-22')

    def test_convert(self):
        eq_(fields.DateField().convert('2013-11-22'),
            datetime.date(2013, 11, 22))
        eq_(fields.DateField().convert('2013-11-22T12:34:56'),
            datetime.date(2013, 11, 22))

    def test_index(self):
        field = fields.DateField(index='no')
        eq_(field.get_definition()['index'], 'no')

    def test_store(self):
        field = fields.DateField(store='yes')
        eq_(field.get_definition()['store'], 'yes')

    def test_boost(self):
        field = fields.DateField(boost=2.5)
        eq_(field.get_definition()['boost'], 2.5)
        field = fields.DateField(boost='2.5')
        eq_(field.get_definition()['boost'], 2.5)

    def test_null_value(self):
        field = fields.DateField(null_value='2013-11-22')
        eq_(field.get_definition()['null_value'], '2013-11-22')

    def test_precision_step(self):
        field = fields.IntegerField(precision_step=4)
        eq_(field.get_definition()['precision_step'], 4)

    def test_boolean_attributes(self):
        for attr in ('ignore_malformed', 'include_in_all'):
            # Test truthiness.
            field = fields.FloatField(**{attr: True})
            eq_(field.get_definition()[attr], True)
            field = fields.FloatField(**{attr: 'true'})
            eq_(field.get_definition()[attr], True)
            # Test falsiness.
            field = fields.FloatField(**{attr: False})
            eq_(field.get_definition()[attr], False)
            field = fields.FloatField(**{attr: ''})
            eq_(field.get_definition()[attr], False)


class TestDateTimeField(TestCase):

    def test_type(self):
        eq_(fields.DateTimeField().field_type, 'date')

    def test_prepare(self):
        eq_(fields.DateTimeField().prepare(
            datetime.datetime(2013, 11, 22, 12, 34, 56)),
            '2013-11-22T12:34:56')

    def test_convert(self):
        eq_(fields.DateTimeField().convert('2013-11-22T12:34:56'),
            datetime.datetime(2013, 11, 22, 12, 34, 56))

    def test_index(self):
        field = fields.DateTimeField(index='no')
        eq_(field.get_definition()['index'], 'no')

    def test_store(self):
        field = fields.DateTimeField(store='yes')
        eq_(field.get_definition()['store'], 'yes')

    def test_boost(self):
        field = fields.DateTimeField(boost=2.5)
        eq_(field.get_definition()['boost'], 2.5)
        field = fields.DateTimeField(boost='2.5')
        eq_(field.get_definition()['boost'], 2.5)

    def test_null_value(self):
        field = fields.DateTimeField(null_value='2013-11-22')
        eq_(field.get_definition()['null_value'], '2013-11-22')

    def test_precision_step(self):
        field = fields.IntegerField(precision_step=4)
        eq_(field.get_definition()['precision_step'], 4)

    def test_boolean_attributes(self):
        for attr in ('ignore_malformed', 'include_in_all'):
            # Test truthiness.
            field = fields.FloatField(**{attr: True})
            eq_(field.get_definition()[attr], True)
            field = fields.FloatField(**{attr: 'true'})
            eq_(field.get_definition()[attr], True)
            # Test falsiness.
            field = fields.FloatField(**{attr: False})
            eq_(field.get_definition()[attr], False)
            field = fields.FloatField(**{attr: ''})
            eq_(field.get_definition()[attr], False)


class TestBinaryField(TestCase):

    def test_type(self):
        eq_(fields.BinaryField().field_type, 'binary')

    def test_prepare(self):
        eq_(fields.BinaryField().prepare(None), None)
        eq_(fields.BinaryField().prepare('test'), base64.b64encode('test'))

    def test_convert(self):
        eq_(fields.BinaryField().convert(None), None)
        eq_(fields.BinaryField().convert(base64.b64encode('test')), 'test')
