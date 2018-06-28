import unittest

import pynmea2
from nose.tools import eq_, ok_

from buoy.client.device.weatherstation.pb200 import WIMDA
from datetime import datetime
from decimal import Decimal
import json


class TestProtocolNMEA0183(unittest.TestCase):
    def setUp(self):
        self.data = {
            'id': None,
            'date': '2017-11-29T10:18:48.714+00:00',
            'air_temp': '26.8',
            'press_inch': '30.327',
            'press_bar': '1.027',
            'water_temp': '20.1',
            'rel_humidity': '12.3',
            'abs_humidity': '21.0',
            'dew_point': '2.3',
            'wind_dir_true': '2.0',
            'wind_dir_magnetic': '128.7',
            'wind_knots': '134.6',
            'wind_meters': '0.3'
        }

        self.item_expected = WIMDA(**self.data)

    def test_wimda_properties(self):

        item = WIMDA(**self.data)

        for name in dir(item):
            value = getattr(item, name)
            if type(value) is datetime:
                eq_(True, True)
            elif type(value) is Decimal:
                eq_(value, Decimal(self.data[name]))
            else:
                eq_(value, self.data[name])

    def test_wimda_fulled(self):

        mda = pynmea2.MDA('WI', 'MDA', (
            self.data['press_inch'], 'I', self.data['press_bar'], 'B',
            self.data['air_temp'], 'C', self.data['water_temp'], 'C', self.data['rel_humidity'],
            self.data['abs_humidity'], self.data['dew_point'], 'C', self.data['wind_dir_true'], 'T',
            self.data['wind_dir_magnetic'], 'M', self.data['wind_knots'], 'N',
            self.data['wind_meters'], 'M'))

        item = WIMDA.from_nmea(self.data['date'], mda)

        eq_(item, self.item_expected)

    def test_wimda_incompleted(self):
        del self.data['water_temp']
        del self.data['rel_humidity']

        item = WIMDA(**self.data)

        ok_(not getattr(item, 'water_temp'))
        ok_(not getattr(item, 'rel_humidity'))
        
    def test_wimda_serialize(self):
        serial = self.item_expected.to_json()

        json_expected = ('"abs_humidity":{abs_humidity},'
                         '"air_temp":{air_temp},'
                         '"date":"{date}",'
                         '"dew_point":{dew_point},'
                         '"press_bar":{press_bar},'
                         '"press_inch":{press_inch},'
                         '"rel_humidity":{rel_humidity},'
                         '"water_temp":{water_temp},'
                         '"wind_dir_magnetic":{wind_dir_magnetic},'
                         '"wind_dir_true":{wind_dir_true},'
                         '"wind_knots":{wind_knots},'
                         '"wind_meters":{wind_meters}').format(**self.data)

        ok_(json_expected in str(serial))

    def test_wimda_deserialize(self):
        json_in = ('{"id": 2, "abs_humidity": 21.0, "air_temp": 26.8, "press_bar": 1.027,'
                   '"press_inch": 30.3273, "date": "2017-02-14 12:46:32.584366", "dew_point": 2.3,'
                   '"rel_humidity": 12.3, "water_temp": 20.1, "wind_dir_magnetic": 128.7, '
                   '"wind_dir_true": 2.0, "wind_knots": 134.6, "wind_meters": 0.3}')

        a = json.loads(json_in)

        item = WIMDA(**a)

        eq_(item.id, 2)
        eq_(item.wind_knots, Decimal(134.6))


if __name__ == '__main__':
    unittest.main()

