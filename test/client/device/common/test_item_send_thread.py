import unittest
from datetime import datetime, timezone
from queue import Queue
from unittest.mock import patch, MagicMock

from nose.tools import eq_, ok_

from buoy.client.device.common.base import MqttThread
from buoy.client.device.common.database import DeviceDB
from buoy.client.device.common.nmea0183 import WIMDA
from buoy.client.notification.client.common import NoticePriorityQueue


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


class TestMqttThread(unittest.TestCase):
    def setUp(self):
        self.cls = WIMDA
        self.topic = "redmic/data"
        self.qos = 1

    @patch.object(MqttThread, 'is_connected_to_mqtt', return_value=False)
    @patch.object(MqttThread, 'send')
    def test_onceCallToConnectMqtt_when_inititializeThread(self, mock_send, mock_is_connected_to_mqtt):
        thread = MqttThread(db=FakeDeviceDB(), queue_send_data=Queue(), queue_data_sent=Queue(),
                            queue_notice=NoticePriorityQueue())
        thread.activity()

        eq_(mock_is_connected_to_mqtt.call_count, 1)
        eq_(mock_send.call_count, 0)

    def test_deleteItemInLimbo_when_itemSuccessPublished(self):
        thread = MqttThread(db=FakeDeviceDB(), queue_send_data=Queue(), queue_data_sent=Queue(),
                            queue_notice=NoticePriorityQueue())
        items = get_items(2)
        for idx, item in enumerate(items):
            thread.limbo.add(idx, item)

        thread.on_publish(None, None, 1)

        eq_(thread.limbo.size(), 1)
        ok_(thread.limbo.get(1) is None)

    def test_isConnectIsTrue_when_onConnectCallbackReceiveRCEqualZero(self):
        thread = MqttThread(db=FakeDeviceDB(), queue_send_data=Queue(), queue_data_sent=Queue(),
                            queue_notice=NoticePriorityQueue())
        items = get_items(2)
        for idx, item in enumerate(items):
            thread.limbo.add(idx, item)

        thread.on_connect(None, None, flags={"session present": 1}, rc=0)
        ok_(thread.is_connected_to_mqtt())

    def test_isConnectIsFalse_when_onConnectCallbackReceiveRcDistinctZero(self):
        thread = MqttThread(db=FakeDeviceDB(), queue_send_data=Queue(), queue_data_sent=Queue(),
                            queue_notice=NoticePriorityQueue())
        items = get_items(2)

        for idx, item in enumerate(items):
            thread.limbo.add(idx, item)

        rc = 1

        thread.on_connect(None, None, None, rc)
        ok_(thread.is_connected_to_mqtt() is False)

    def test_clearLimboAndStopThread_when_disconnectMqttOk(self):
        thread = MqttThread(db=FakeDeviceDB(), queue_send_data=Queue(), queue_data_sent=Queue(),
                            queue_notice=NoticePriorityQueue())
        items = get_items(2)

        thread.active = True

        for idx, item in enumerate(items):
            thread.limbo.add(idx, item)

        client = FakeMQTT()
        client.loop_stop = MagicMock()

        thread.on_disconnect(client, None, 0)
        ok_(thread.is_connected_to_mqtt() is False)
        ok_(thread.is_active() is False)
        eq_(thread.limbo.size(), 0)

    def test_clearLimboAndDontStopThread_when_disconnectMqttKO(self):
        thread = MqttThread(db=FakeDeviceDB(), queue_send_data=Queue(), queue_data_sent=Queue(),
                            queue_notice=NoticePriorityQueue())
        items = get_items(2)

        thread.active = True

        for idx, item in enumerate(items):
            thread.limbo.add(idx, item)

        client = FakeMQTT()

        thread.on_disconnect(client, None, 1)
        ok_(thread.is_connected_to_mqtt() is False)
        ok_(thread.is_active() is True)
        eq_(thread.limbo.size(), 0)

    def test_send(self):
        thread = MqttThread(db=FakeDeviceDB(), queue_send_data=Queue(), queue_data_sent=Queue(),
                            queue_notice=NoticePriorityQueue())
        item = get_item()

        client = FakeMQTT()
        client.publish = MagicMock(return_value=FakeReponseMQTT(rc={"mid": 0}))

        thread.send(item)
        eq_(thread.limbo.size(), 1)


if __name__ == '__main__':
    unittest.main()
