"""Booking.com API Client"""

import os
import xmltodict
import requests


class BaseEndPointIterator(object):
    """Since booking.com api only lets us to fetch api data page by page in
    number of rows, this base iterator class helps iterating through the pages
    by given offset and number of rows. Subclasses must provide
    ``_fetch_buffer`` which actually fetches booking.com api data.

    :Example:

    >>> class MyIterator(BaseEndPointIterator):
            def _fetch_buffer(self):
                client = MockClient()
                return client.fetch(endpoint=self.endpoint, offset=self.offset,
                                    rows=self.rows)
    >>> [country.name for country in MyBookingcomIterator('getCountries')]
    ['Albenia', 'Austria']

    """
    _MAX_ROWS = 1000

    def __init__(self, end_point, rows=None):
        """Constructor

        :param end_point: name of api end point
        :type end_point: str

        :param rows: number of rows per page
        :type rows: int

        """
        self.end_point = end_point
        self.rows = rows or self._MAX_ROWS
        self.buffer = None
        self.cursor = 0
        self.offset = 0

    def __iter__(self):
        """Implements ``iterable`` interface by referencing ``self`` is an
        ``iterator``

        """
        return self

    def next(self):
        """Implements ``iterator`` interface"""
        current = None
        if not self.buffer:
            self.buffer = self._fetch_buffer()
        bufferlen = len(self.buffer) if self.buffer else 0
        if self.cursor < bufferlen:
            current = self.buffer[self.cursor]
            self.cursor = self.cursor + 1
            if self.cursor == bufferlen == self.rows:
                self.offset = self.offset + self.rows
                self.cursor = 0
                self.buffer = self._fetch_buffer()
            return current
        else:
            self.offset = 0
            self.cursor = 0
            raise StopIteration()

    def _fetch_buffer(self):
        """Subclasses have to implement this method. This method must provide
        booking.com data for given offset and number of rows

        :returns: List of objects in result of api endpoint call
        :rtype: list

        """
        raise NotImplementedError()


class FilesystemEndPointIterator(BaseEndPointIterator):
    """``BaseEndPointIterator`` implemetation uses pre-fetched files on
    filesystem provides booking.com api data

    """
    def __init__(self, end_point, rows=None, data_dir='/tmp/bookingcom/'):
        """Constructor

        :param data_dir: directory path contains the booking.com static data
        :param type: str

        """
        super(FilesystemEndPointIterator, self).__init__(end_point, rows=rows)
        self.data_dir = data_dir

    def _fetch_buffer(self):
        """Fetch data from pre-fetched booking.com api offset files"""
        buffer = None
        path = os.path.join(self.data_dir, self.end_point,
                            'offset_%s.xml' % self.offset)
        if os.path.exists(path):
            f = open(path, 'r')
            try:
                xml = f.read()
            except IOError:
                pass
            finally:
                f.close()
            buffer = xmltodict.parse(xml).get(self.end_point).get('result',
                                                                  None)
        return buffer


class XmlRpcEndPointIterator(BaseEndPointIterator):
    """``BaseEndPointIterator`` implemetation uses ``XmlRpcClient`` to fetch
    booking.com api data

    """
    BASE_URL = 'http://distribution-xml.booking.com/xml/'

    def __init__(self, end_point, rows=None, base_url=None, username=None,
                 password=None):
        """Constructor

        :param base_url: base api url
        :param type: str

        :param username: api username
        :param type: str

        :param password: api password
        :param type: str

        """
        super(XmlRpcEndPointIterator, self).__init__(end_point, rows=rows)
        self.base_url = base_url or self.BASE_URL
        self.username = username
        self.password = password

    @classmethod
    def create_url(klass, end_point, base_url=None):
        return '%sbookings.%s' % (base_url or klass.BASE_URL, end_point)

    def _fetch_buffer(self):
        """Fetch data from actual booking.com api"""
        url = XmlRpcEndPointIterator.create_url(self.end_point)
        response = requests.post(url, auth=(self.username, self.password),
                                 params={'offset': self.offset,
                                         'rows': self.rows})
        response.raise_for_status()
        payload = xmltodict.parse(response.text)
        buffer = payload.get(self.end_point).get('result', None)
        return buffer


class BookingcomClient(object):
    """Bookingcom Api Client based on endpoint iterators which defines one per
    API endpoint automatically

    :Example:
    >>> client = BookingcomApiClient()
    >>> [country.name for country in client.getCountries()]
    ['Albenia', 'Austria']
    """

    _END_POINTS = (
        'getCities',
        'getCountries',
        'getDistricts',
        'getDistrictHotels',
        'getFacilityTypes',
        'getHotelDescriptionPhotos',
        'getHotelDescriptionTranslations',
        'getHotelDescriptionTypes',
        'getHotelFacilities',
        'getHotelFacilityTypes',
        'getHotelLogoPhotos',
        'getHotelPhotos',
        'getHotelTranslations',
        'getHotelTypes',
        'getHotels',
        'getRegions',
        'getRegionHotels',
        'getRooms',
        'getRoomTypes',
        'getRoomFacilityTypes',
        'getRoomFacilities',
        'getRoomTranslations',
        'getRoomPhotos',
    )

    def __init__(self, end_point_iterator_class=FilesystemEndPointIterator,
                 **kwargs):
        """Constructor

        :param end_point_iterator_class: end point iterator class
        :type end_point_iterator_class: class
        """

        def generate_end_point_iterator(end_point):
            def aux(rows=None):
                rows = rows or BaseEndPointIterator._MAX_ROWS
                return end_point_iterator_class(end_point, rows, **kwargs)
            return aux

        for end_point in self._END_POINTS:
            setattr(self, end_point, generate_end_point_iterator(end_point))
