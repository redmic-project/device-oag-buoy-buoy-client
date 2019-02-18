import unittest
from datetime import datetime, timezone
from queue import Queue
from unittest.mock import patch, call

from nose.tools import eq_

from buoy.client.device.common.item import ItemQueue
from buoy.client.device.common.base import ItemSaveThread
from buoy.client.device.common.nmea0183 import WIMDA
from buoy.client.notification.client.common import NoticePriorityQueue


def get_items(num=1):
    items = []
    for i in range(0, num):
        data = {
            'id': i,
            'datetime': datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
            'air_temperature': '26.8',
            'barometric_pressure_inch': '30.3273',
            'barometric_pressure_bar': '1.027',
            'water_temperature': '20.1',
            'rel_humidity': '12.3',
            'abs_humidity': '21.0',
            'dew_point': '2.3',
            'wind_dir_true': '2.0',
            'wind_dir_magnetic': '128.7',
            'wind_knots': '134.6',
            'wind_meters': '0.3'
        }

        items.append(WIMDA(**data))

    return items


class TestItemSaveThread(unittest.TestCase):
    @patch.object(ItemSaveThread, 'save')
    @patch.object(ItemSaveThread, 'is_active', side_effect=[True, True, True, False])
    def test_twiceCallSaveMethodAndExitsTwoItemsInNoticeQueue_when_insertTwoItemsInQueueData(self,
                                                                                             mock_is_active, mock_save):
        queue_data = Queue()
        queue_notice = NoticePriorityQueue()

        items_expected = []
        for item in get_items(2):
            x = ItemQueue(item=item)
            queue_data.put_nowait(x)
            items_expected.append(call(x))

        thread = ItemSaveThread(queue_save_data=queue_data, db=None, queue_notice=queue_notice)
        thread.run()

        eq_(mock_is_active.call_count, 4)
        eq_(mock_save.call_count, 2)
        eq_(mock_save.call_args_list, items_expected)


if __name__ == '__main__':
    unittest.main()
