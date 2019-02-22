import unittest
from datetime import datetime, timezone
from decimal import Decimal
from queue import Queue
from unittest.mock import patch

from nose.tools import eq_, ok_

from buoy.client.device.currentmeter.acmplus import ACMPlusReader
from buoy.client.device.currentmeter.item import ACMPlusItem
from uuid import uuid4


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

    @patch('buoy.client.device.common.base.Device')
    def test_queueSizeEqualToOne_when_parseOneItem(self, mock_device):
        now = datetime.now(tz=timezone.utc)
        date_format = "%H:%M:%S, %m-%d-%Y"
        data = {
            'date': now.strftime(date_format),
            'vx': Decimal(-73.51),
            'vy': Decimal(-0.61),
            'water_temp': Decimal(24.37)
        }
        reader = ACMPlusReader(device=mock_device, queue_save_data=Queue(), queue_send_data=Queue(),
                               queue_notice=Queue(), queue_exceptions=Queue())
        buffer = "{vy}, {vx}, {date}, {water_temp}".format(**data) + reader.char_splitter
        reader.buffer = buffer

        reader.process_data()

        eq_(reader.queue_save_data.qsize(), 1)
        eq_(reader.queue_send_data.qsize(), 1)

    def test_convertToJson(self):
        now = datetime.now(tz=timezone.utc)
        data_expected = {
            'uuid': uuid4(),
            'date': now.isoformat(timespec='milliseconds'),
            'vx': -73.51,
            'vy': -0.61,
            'water_temp': 24.37,
            'direction': 269.525,
            'speed': 73.513
        }
        data = {
            'uuid': data_expected['uuid'],
            'date': data_expected['date'],
            'vx': Decimal(data_expected['vx']),
            'vy': Decimal(data_expected['vy']),
            'water_temp': Decimal(data_expected['water_temp'])
        }

        json = ACMPlusItem(**data).to_json()
        json_expected = ('"date":"{date}",'
                         '"direction":{direction},'
                         '"speed":{speed},'
                         '"uuid":"{uuid}",'
                         '"vx":{vx},'
                         '"vy":{vy},'
                         '"water_temp":{water_temp}').format(**data_expected)

        ok_(json_expected in json)


if __name__ == '__main__':
    unittest.main()
