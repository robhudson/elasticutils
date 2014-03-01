import base64
import datetime
from decimal import Decimal
from unittest import TestCase

from nose.tools import eq_

from elasticutils import fields


class TestStringField(TestCase):

    def test_type(self):
        eq_(fields.StringField().field_type, 'string')

    def test_to_es(self):
        eq_(fields.StringField().to_es(None), None)
        eq_(fields.StringField().to_es('test'), 'test')

    def test_to_python(self):
        eq_(fields.StringField().to_python(None), None)
        eq_(fields.StringField().to_python('test'), 'test')

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

    def test_null_value(self):
        field = fields.StringField(null_value='na')
        eq_(field.get_definition()['null_value'], 'na')

    def test_boolean_attributes(self):
        for attr in ('omit_norms', 'include_in_all'):
            field = fields.StringField(**{attr: True})
            eq_(field.get_definition()[attr], True)
            field = fields.StringField(**{attr: False})
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


class TestIntegerField(TestCase):

    def test_type(self):
        eq_(fields.IntegerField().field_type, 'integer')
        eq_(fields.IntegerField(type='byte').field_type, 'byte')
        eq_(fields.IntegerField(type='short').field_type, 'short')
        eq_(fields.IntegerField(type='long').field_type, 'long')
        eq_(fields.IntegerField(type='foo').field_type, 'integer')

    def test_to_es(self):
        eq_(fields.IntegerField().to_python(None), None)
        eq_(fields.IntegerField().to_es(100), 100)
        eq_(fields.IntegerField().to_es('100'), 100)

    def test_to_python(self):
        eq_(fields.IntegerField().to_python(None), None)
        eq_(fields.IntegerField().to_python(100), 100)
        eq_(fields.IntegerField().to_es('100'), 100)

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

    def test_null_value(self):
        field = fields.IntegerField(null_value=1)
        eq_(field.get_definition()['null_value'], 1)

    def test_boolean_attributes(self):
        for attr in ('ignore_malformed', 'include_in_all'):
            field = fields.IntegerField(**{attr: True})
            eq_(field.get_definition()[attr], True)
            field = fields.IntegerField(**{attr: False})
            eq_(field.get_definition()[attr], False)


class TestFloatField(TestCase):

    def test_type(self):
        eq_(fields.FloatField().field_type, 'float')
        eq_(fields.FloatField(type='double').field_type, 'double')
        eq_(fields.FloatField(type='foo').field_type, 'float')

    def test_to_es(self):
        eq_(fields.FloatField().to_python(None), None)
        eq_(fields.FloatField().to_es(100), 100.0)
        eq_(fields.FloatField().to_es('100'), 100.0)

    def test_to_python(self):
        eq_(fields.FloatField().to_python(None), None)
        eq_(fields.FloatField().to_python(100), 100.0)
        eq_(fields.FloatField().to_es('100'), 100.0)

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

    def test_null_value(self):
        field = fields.FloatField(null_value=1.0)
        eq_(field.get_definition()['null_value'], 1.0)

    def test_boolean_attributes(self):
        for attr in ('ignore_malformed', 'include_in_all'):
            field = fields.FloatField(**{attr: True})
            eq_(field.get_definition()[attr], True)
            field = fields.FloatField(**{attr: False})
            eq_(field.get_definition()[attr], False)


class TestDecimalField(TestCase):
    """DecimalField subclasses StringField, so we just test a few things."""

    def test_type(self):
        eq_(fields.DecimalField().field_type, 'string')

    def test_to_es(self):
        eq_(fields.DecimalField().to_python(None), None)
        eq_(fields.DecimalField().to_es(Decimal('100.0')), '100.0')
        eq_(fields.DecimalField().to_es(Decimal('100')), '100.0')

    def test_to_python(self):
        eq_(fields.DecimalField().to_python(None), None)
        eq_(fields.DecimalField().to_python('100.0'), Decimal('100.0'))


class TestBooleanField(TestCase):

    def test_type(self):
        eq_(fields.BooleanField().field_type, 'boolean')

    def test_to_es(self):
        eq_(fields.BooleanField().to_python(None), None)
        eq_(fields.BooleanField().to_es(True), True)
        eq_(fields.BooleanField().to_es(False), False)

    def test_to_python(self):
        eq_(fields.BooleanField().to_python(None), None)
        eq_(fields.BooleanField().to_python(True), True)
        eq_(fields.BooleanField().to_python(False), False)

    def test_index(self):
        field = fields.BooleanField(index='no')
        eq_(field.get_definition()['index'], 'no')

    def test_store(self):
        field = fields.BooleanField(store='yes')
        eq_(field.get_definition()['store'], 'yes')

    def test_boost(self):
        field = fields.BooleanField(boost=2.5)
        eq_(field.get_definition()['boost'], 2.5)

    def test_null_value(self):
        field = fields.BooleanField(null_value=True)
        eq_(field.get_definition()['null_value'], True)

    def test_boolean_attributes(self):
        field = fields.BooleanField(include_in_all=True)
        eq_(field.get_definition()['include_in_all'], True)
        field = fields.BooleanField(include_in_all=False)
        eq_(field.get_definition()['include_in_all'], False)


class TestDateField(TestCase):

    def test_type(self):
        eq_(fields.DateField().field_type, 'date')

    def test_to_es(self):
        eq_(fields.DateField().to_es(datetime.date(2013, 11, 22)),
            '2013-11-22')

    def test_to_python(self):
        eq_(fields.DateField().to_python(None), None)
        eq_(fields.DateField().to_python('2013-11-22'),
            datetime.date(2013, 11, 22))
        eq_(fields.DateField().to_python('2013-11-22T12:34:56'),
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

    def test_null_value(self):
        field = fields.DateField(null_value='2013-11-22')
        eq_(field.get_definition()['null_value'], '2013-11-22')

    def test_precision_step(self):
        field = fields.IntegerField(precision_step=4)
        eq_(field.get_definition()['precision_step'], 4)

    def test_boolean_attributes(self):
        for attr in ('ignore_malformed', 'include_in_all'):
            field = fields.FloatField(**{attr: True})
            eq_(field.get_definition()[attr], True)
            field = fields.FloatField(**{attr: False})
            eq_(field.get_definition()[attr], False)


class TestDateTimeField(TestCase):

    def test_type(self):
        eq_(fields.DateTimeField().field_type, 'date')

    def test_to_es(self):
        eq_(fields.DateTimeField().to_es(
            datetime.datetime(2013, 11, 22, 12, 34, 56)),
            '2013-11-22T12:34:56')

    def test_to_python(self):
        eq_(fields.DateTimeField().to_python(None), None)
        eq_(fields.DateTimeField().to_python('2013-11-22T12:34:56'),
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

    def test_null_value(self):
        field = fields.DateTimeField(null_value='2013-11-22')
        eq_(field.get_definition()['null_value'], '2013-11-22')

    def test_precision_step(self):
        field = fields.IntegerField(precision_step=4)
        eq_(field.get_definition()['precision_step'], 4)

    def test_boolean_attributes(self):
        for attr in ('ignore_malformed', 'include_in_all'):
            field = fields.FloatField(**{attr: True})
            eq_(field.get_definition()[attr], True)
            field = fields.FloatField(**{attr: False})
            eq_(field.get_definition()[attr], False)


class TestBinaryField(TestCase):

    def test_type(self):
        eq_(fields.BinaryField().field_type, 'binary')

    def test_to_es(self):
        eq_(fields.BinaryField().to_es(None), None)
        eq_(fields.BinaryField().to_es('test'), base64.b64encode('test'))

    def test_to_python(self):
        eq_(fields.BinaryField().to_python(None), None)
        eq_(fields.BinaryField().to_python(base64.b64encode('test')), 'test')
