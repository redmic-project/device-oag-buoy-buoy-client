import unittest
from datetime import datetime, timezone
from decimal import Decimal
from queue import Queue
from unittest.mock import patch

from nose.tools import eq_

from buoy.client.device.currentmeter.acmplus import ACMPlusReader
from buoy.client.device.currentmeter.item import ACMPlusItem


class TestACMPlusReader(unittest.TestCase):
    @patch('buoy.client.device.common.base.Device')
    def test_parser(self, mock_device):
        now = datetime.now(tz=timezone.utc)
        date_format = "%H:%M:%S, %m-%d-%Y"
        data = {
            'date': now.strftime(date_format),
            'vx': Decimal(-73.51),
            'vy': Decimal(-0.61),
            'water_temp': Decimal(24.37)
        }

        line = "{vy}, {vx}, {date}, {water_temp}".format(**data)
        item = ACMPlusReader(device=mock_device, queue_save_data=Queue(), queue_notice=Queue(),
                             queue_exceptions=Queue()).parser(line)

        for key, value in data.items():
            if key == 'date':
                eq_(getattr(item, key).strftime(date_format), now.strftime(date_format))
            else:
                eq_(getattr(item, key), value)

    def test_convertToJson(self):
        matching = {
            'vx': 50,
            'vy': 51
        }

        ivd = {v: k for k, v in matching.items()}

        now = datetime.now(tz=timezone.utc)
        date_format = "%H:%M:%S, %m-%d-%Y"
        data = {
            'date': now.strftime(date_format),
            'vx': Decimal(-73.51),
            'vy': Decimal(-0.61),
            'water_temp': Decimal(24.37)
        }

        item = ACMPlusItem(**data).to_json()


if __name__ == '__main__':
    unittest.main()
