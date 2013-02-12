import unittest
from mock import patch
from httpretty import HTTPretty, httprettified

from bookingcom import (BookingcomClient, XmlRpcEndPointIterator,
                        FilesystemEndPointIterator)


class BookingcomTest(unittest.TestCase):

    _FIXTURE_OFFSET_FIRST = """<?xml version="1.0" standalone="yes"?>
<getCountries>
  <result>
    <area>Europe</area>
    <countrycode>ad</countrycode>
    <languagecode>en</languagecode>
    <name>Andorra</name>
  </result>
  <result>
    <area>Middle East</area>
    <countrycode>ae</countrycode>
    <languagecode>en</languagecode>
    <name>United Arab Emirates</name>
  </result>
  <result>
    <area>Caribbean</area>
    <countrycode>ag</countrycode>
    <languagecode>en</languagecode>
    <name>Antigua &amp; Barbuda</name>
  </result>
</getCountries>
"""

    _FIXTURE_OFFSET_LATTER = """<?xml version="1.0" standalone="yes"?>
<getCountries>
  <result>
    <area>Caribbean</area>
    <countrycode>ai</countrycode>
    <languagecode>en</languagecode>
    <name>Anguilla</name>
  </result>
  <result>
    <area>Europe</area>
    <countrycode>al</countrycode>
    <languagecode>en</languagecode>
    <name>Albania</name>
  </result>
</getCountries>
"""

    @httprettified
    def test_xmlrpciterator(self):
        """Tests bookingcom api client using xml rcp iterator"""
        mock_url = XmlRpcEndPointIterator.create_url('getCountries')
        HTTPretty.register_uri(HTTPretty.POST, mock_url, responses=[
            HTTPretty.Response(body=self._FIXTURE_OFFSET_FIRST),
            HTTPretty.Response(body=self._FIXTURE_OFFSET_LATTER)])
        client = BookingcomClient(
            end_point_iterator_class=XmlRpcEndPointIterator)
        countries = list(client.getCountries(rows=3))
        self.assertEqual(len(countries), 5)
        self.assertEqual(countries[0]['countrycode'], 'ad')
        self.assertEqual(countries[0]['name'], 'Andorra')
        self.assertEqual(countries[4]['countrycode'], 'al')
        self.assertEqual(countries[4]['name'], 'Albania')

    def test_filesystemiterator(self):
        """Tests bookingcom api client using file system iterator"""
        with patch('__builtin__.open') as open_mock:
            with patch('os.path.exists', return_value=True):
                open_mock.return_value.read.side_effect = \
                    [self._FIXTURE_OFFSET_FIRST, self._FIXTURE_OFFSET_LATTER]
                client = BookingcomClient(
                    end_point_iterator_class=FilesystemEndPointIterator)
                countries = list(client.getCountries(rows=3))
                self.assertEqual(len(countries), 5)
                self.assertEqual(countries[0]['countrycode'], 'ad')
                self.assertEqual(countries[0]['name'], 'Andorra')
                self.assertEqual(countries[4]['countrycode'], 'al')
                self.assertEqual(countries[4]['name'], 'Albania')
