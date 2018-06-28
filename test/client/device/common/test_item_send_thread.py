import unittest
from datetime import datetime, timezone
from queue import Queue, Empty
from unittest.mock import patch, MagicMock

from nose.tools import eq_

from buoy.client.device.common.base import ItemSendThread
from buoy.client.device.common.database import DeviceDB
from buoy.client.device.common.nmea0183 import WIMDA
from buoy.client.notification.client.common import NoticePriorityQueue


def get_items(num=1):
    items = []
    for i in range(0, num):
        data = {
            'id': i,
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
        item = WIMDA(**data)
        items.append(item)

    return items


class FakeDeviceDB(DeviceDB):
    def __init__(self):
        pass


class FakeReponseMQTT(object):
    def __init__(self, rc=0):
        self.rc = rc

    def wait_for_publish(self):
        pass


class FakeMQTT(object):
    def __init__(self):
        pass

    def disconnect(self):
        pass


class TestItemSendThread(unittest.TestCase):
    def setUp(self):
        self.queue_send = Queue()
        self.queue_notice = NoticePriorityQueue()
        self.db = FakeDeviceDB()
        self.cls = WIMDA
        self.topic = "redmic/data"
        self.qos = 1
        self.thread = ItemSendThread(db=self.db, queue_send_data=self.queue_send, queue_notice=self.queue_notice,
                                     topic_data=self.topic, qos=self.qos)

    def tearDown(self):
        self.thread.stop()

    def test_returnOneItem_when_existsItemsInQueue(self):
        items_expected = get_items(2)
        for item in items_expected:
            self.queue_send.put_nowait(item)

        self.thread.active = True
        items = self.thread.waiting_data()

        eq_(len(items), 1)
        eq_(items[0], items_expected[0])

    def test_returnTwoItem_when_notExistsItemsInQueueButExistsDataInDB(self):
        items_expected = get_items(2)
        self.db.get_items_to_send = MagicMock(return_value=items_expected)
        self.thread.active = True
        items = self.thread.waiting_data()

        eq_(len(items), 2)
        eq_(items, items_expected)

    @patch.object(ItemSendThread, 'is_active', side_effect=[True, True, False])
    def test_returnEmptyArray_when_notExistsItemsToSend(self, mock_is_active):
        self.db.get_items_to_send = MagicMock(return_value=[])
        self.queue_send.get = MagicMock(side_effect=Empty())
        items = self.thread.waiting_data()

        eq_(len(items), 0)
        eq_(self.db.get_items_to_send.call_count, 2)
        eq_(self.queue_send.get.call_count, 2)

    def test_shouldChangeItemStatusToSended_when_publishItemOK(self):
        item = get_items()[0]
        item_to_sent = str(item.to_json())

        self.db.set_sent = MagicMock(return_value=[item.id])
        self.queue_send.put_nowait(item)
        self.thread.client = FakeMQTT()
        self.thread.client.publish = MagicMock(return_value=FakeReponseMQTT())

        self.thread.send(item)

        eq_(self.db.set_sent.call_count, 1)
        self.db.set_sent.assert_called_with(item.id)
        eq_(self.thread.client.publish.call_count, 1)
        self.thread.client.publish.assert_called_with(self.topic, item_to_sent, qos=self.qos)

    def test_shouldChangeItemStatusToError_when_publishItemKO(self):
        item = get_items()[0]
        item_to_sent = str(item.to_json())

        self.db.set_sent = MagicMock(return_value=[item.id])
        self.db.set_failed = MagicMock(return_value=[item.id])
        self.queue_send.put_nowait(item)
        self.thread.client = FakeMQTT()
        self.thread.client.publish = MagicMock(return_value=FakeReponseMQTT(rc=1))

        self.thread.send(item)

        eq_(self.db.set_sent.call_count, 0)
        eq_(self.db.set_failed.call_count, 1)
        self.db.set_failed.assert_called_with(item.id)
        eq_(self.thread.client.publish.call_count, 1)
        self.thread.client.publish.assert_called_with(self.topic, item_to_sent, qos=self.qos)


if __name__ == '__main__':
    unittest.main()
