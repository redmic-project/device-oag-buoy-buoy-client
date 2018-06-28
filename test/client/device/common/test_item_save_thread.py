import unittest
from datetime import datetime, timezone
from queue import Queue
from unittest.mock import patch, call, Mock

from nose.tools import eq_

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
        queue_send = Queue()
        queue_notice = NoticePriorityQueue()

        items_expected = []
        for item in get_items(2):
            queue_data.put_nowait(item)
            items_expected.append(call(item))

        thread = ItemSaveThread(queue_save_data=queue_data, queue_send_data=queue_send,
                                db=None, queue_notice=queue_notice)
        thread.run()

        eq_(mock_is_active.call_count, 4)
        eq_(queue_send.qsize(), 2)
        eq_(mock_save.call_count, 2)
        eq_(mock_save.call_args_list, items_expected)

    @patch.object(ItemSaveThread, 'save')
    @patch.object(ItemSaveThread, 'is_active')
    def test_call4TimesSaveMethodAndOnceSendMethod_when_queueSendIsFull(self, mock_is_active, mock_save):
        NUM_ITEM = 4
        QSIZE = 1

        queue_data = Queue()
        mock_task_done = Mock(return_value=None)
        queue_data.task_done = mock_task_done

        queue_send = Queue(maxsize=1)
        queue_notice = NoticePriorityQueue()

        items_expected = []
        is_active = []
        for item in get_items(NUM_ITEM):
            queue_data.put_nowait(item)
            items_expected.append(call(item))
            is_active.append(True)

        is_active.append(False)
        mock_is_active.side_effect = is_active

        thread = ItemSaveThread(queue_save_data=queue_data, queue_send_data=queue_send,
                                db=None, queue_notice=queue_notice)
        thread.run()

        eq_(mock_is_active.call_count, NUM_ITEM + 1)
        eq_(queue_send.qsize(), QSIZE)
        eq_(mock_save.call_count, NUM_ITEM)
        eq_(mock_task_done.call_count, NUM_ITEM)
        eq_(mock_save.call_args_list, items_expected)


if __name__ == '__main__':
    unittest.main()
