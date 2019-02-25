import unittest
from test.support.function.database import *
from queue import Queue, Full
from unittest.mock import MagicMock

from nose.tools import eq_

from buoy.client.device.currentmeter.acmplus import ACMPlusItem
from buoy.client.device.common.base import ItemDBToSendThread
from buoy.client.device.common.base import DeviceDB


class TestItemInDBToSendThread(unittest.TestCase):

    def test_noPutItemInQueue_when_queueIsFullInLoop(self):
        queue_notice = Queue()
        queue_send_data = Queue()
        queue_send_data.put_nowait = MagicMock(side_effect=Full())
        db_conf = prepare_db()
        apply_sql_file('test/support/data/data_example.sql')
        dev_db = DeviceDB(
            db_config=db_conf,
            db_tablename="acmplus",
            cls_item=ACMPlusItem
        )
        thread = ItemDBToSendThread(queue_send_data=queue_send_data, db=dev_db, queue_notice=queue_notice)

        thread.activity()

        eq_(queue_send_data.qsize(), 0)

    def test_putItemInQueue_when_queueIsFullInLoop(self):
        queue_notice = Queue()
        queue_send_data = Queue()
        db_conf = prepare_db()
        apply_sql_file('test/support/data/data_5_items_to_send.sql')
        dev_db = DeviceDB(
            db_config=db_conf,
            db_tablename="acmplus",
            cls_item=ACMPlusItem
        )
        thread = ItemDBToSendThread(queue_send_data=queue_send_data, db=dev_db, queue_notice=queue_notice)

        thread.activity()

        eq_(queue_send_data.qsize(), 5)


if __name__ == '__main__':
    unittest.main()
