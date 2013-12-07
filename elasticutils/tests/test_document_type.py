from unittest import TestCase

from nose.tools import eq_

from elasticutils import DocumentType, fields


class BookDocumentType(DocumentType):

    id = fields.IntegerField(type='long')
    name = fields.StringField(analyzer='snowball')
    name_sort = fields.StringField(index='not_analyzed')
    authors = fields.StringField(is_multivalued=True)
    published_date = fields.DateField()
    price = fields.DecimalField()
    is_autographed = fields.BooleanField()
    sales = fields.IntegerField()


class DocumentTypeTest(TestCase):

    def setUp(self):
        self._type = BookDocumentType

    def test_mapping(self):
        mapping = self._type().get_mapping()

        # Check top level element.
        eq_(mapping.keys(), ['properties'])

        fields = mapping['properties']

        eq_(fields['id']['type'], 'long')
        eq_(fields['name']['type'], 'string')
        eq_(fields['name']['analyzer'], 'snowball')
        eq_(fields['name_sort']['type'], 'string')
        eq_(fields['name_sort']['index'], 'not_analyzed')
        eq_(fields['authors']['type'], 'string')
        eq_(fields['published_date']['type'], 'date')
        eq_(fields['price']['type'], 'string')
        eq_(fields['is_autographed']['type'], 'boolean')
        eq_(fields['sales']['type'], 'integer')
