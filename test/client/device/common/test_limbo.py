import unittest
from datetime import datetime, timezone

from nose.tools import eq_, ok_
from buoy.client.device.common.limbo import Limbo
from buoy.client.device.common.nmea0183 import WIMDA


def get_item():
    data = {
        'date': datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        'air_temp': '26.8',
        'press_inch': '30.3273',
        'pres_bar': '1.027',
        'water_temp': '20.1',
        'rel_humidity': '12.3',
        'abs_humidity': '21.0',
        'dew_point': '2.3',
        'wind_dir_true': '2.0',
        'wind_dir_magnetic': '128.7',
        'wind_knots': '134.6',
        'wind_meters': '0.3'
    }
    return WIMDA(**data)


def get_items(num=2):
    items = []
    for i in range(0, num):
        items.append(get_item())
    return items


class TestMqttThread(unittest.TestCase):

    def test_itemAdded_when_callAddItemLimbo(self):
        limbo = Limbo()
        item = get_item()
        limbo.add(1, item)

        ok_(limbo.exists(1))
        eq_(limbo.size(), 1)

    def test_clearLimbo_when_addedItemsAndClearedLimbo(self):
        limbo = Limbo()

        items = get_items(2)
        for idx, item in enumerate(items):
            limbo.add(idx, item)

        eq_(limbo.size(), 2)
        limbo.clear()
        eq_(limbo.size(), 0)

    def test_returnItem_when_passId(self):
        limbo = Limbo()
        items = get_items(2)
        for idx, item in enumerate(items):
            limbo.add(idx, item)

        eq_(limbo.size(), 2)
        item = limbo.pop(1)
        ok_(item is not None)
        eq_(limbo.size(), 1)
        item = limbo.get(1)
        ok_(item is None)
