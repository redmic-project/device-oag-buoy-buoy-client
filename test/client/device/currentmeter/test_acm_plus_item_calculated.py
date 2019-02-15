import json
import unittest
from datetime import datetime
from decimal import *

from nose.tools import eq_, ok_

from buoy.client.device.currentmeter.acmplus import ACMPlusItem


class TestACMlusItemCalculate(unittest.TestCase):
    def test_calculate_properties(self):
        data = {
            'vx': -45.81,
            'vy': 152.0,
            'speed': 158.753,
            'direction': 343.228
        }

        item = ACMPlusItem(vx=data['vx'], vy=data['vy'])

        for key, value in data.items():
            eq_(round(getattr(item, key), 2), round(Decimal(value), 2))

    def test_calculate_properties_value_zero(self):
        data = {
            'vx': 0,
            'vy': 0.79,
            'speed': 0.79,
            'direction': 0
        }

        item = ACMPlusItem(vx=data['vx'], vy=data['vy'])

        for key, value in data.items():
            eq_(round(getattr(item, key), 2), round(Decimal(value), 2))


class TestACMPlusItem(unittest.TestCase):
    def setUp(self):
        self.data = {
            'uuid': 1,
            'date': '2017-11-29T10:18:48.714+00:00',
            'vx': 0.0,
            'vy': 0.79,
            'water_temp': 18.3
        }

        self.item_expected = ACMPlusItem(**self.data)

    def test_wimda_properties(self):

        item = ACMPlusItem(**self.data)
        self.data['speed'] = 0.79
        self.data['direction'] = 0

        for name in dir(item):
            value = getattr(item, name)
            if type(value) is datetime:
                eq_(True, True)
            elif type(value) is Decimal:
                eq_(value, Decimal(self.data[name]))
            else:
                eq_(value, self.data[name])

    def test_acmplus_item_serialize(self):
        serial = self.item_expected.to_json()

        self.data['speed'] = 0.79
        self.data['direction'] = 0.0

        json_expected = ('"date":"{date}",'
                         '"direction":{direction},'
                         '"speed":{speed},'
                         '"uuid":{uuid},'
                         '"vx":{vx},'
                         '"vy":{vy},'
                         '"water_temp":{water_temp}').format(**self.data)

        ok_(json_expected in str(serial))

    def test_wimda_deserialize(self):
        json_in = ('{"uuid": 2, "direction": 0.0, "speed": 0.79, "vx": 0.0,'
                   '"vy": 0.79, "date": "2017-02-14 12:46:32.584366", "water_temp": 20.1}')

        a = json.loads(json_in)

        item = ACMPlusItem(**a)

        eq_(item.uuid, 2)
        eq_(item.water_temp, Decimal(20.1))


if __name__ == '__main__':
    unittest.main()
