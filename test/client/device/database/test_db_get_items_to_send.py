import unittest

from nose.tools import eq_, ok_

from buoy.client.device.common.base import DeviceDB
from buoy.client.device.common.nmea0183 import WIMDA
from buoy.client.device.currentmeter.acmplus import ACMPlusItem
from test.support.function.database import *


class BaseDBGetItemsTests(unittest.TestCase):
    item_class = None
    db_tablename = None
    db_cls = DeviceDB
    skip_test = False

    @classmethod
    def setUpClass(cls):
        global skip_test

        if cls is BaseDBGetItemsTests:
            skip_test = True
        else:
            skip_test = False

        super(BaseDBGetItemsTests, cls).setUpClass()

    def setUp(self):
        if skip_test:
            self.skipTest("Skip BaseTest tests, it's a base class")

    def tearDown(self):
        """ Called after all of the tests in this file have been executed to close the database connecton and destroy
        the temporary database """

        close_db()

    def test_should_return15Items_when_getItemsToSend(self):
        db_conf = prepare_db()
        apply_sql_file('test/support/data/data_example.sql')

        dev_db = self.db_cls(
            db_config=db_conf,
            db_tablename=self.db_tablename,
            cls_item=self.item_class
        )

        rows = dev_db.get_items_to_send()

        eq_(len(rows), 15)
        ok_(all(a.id <= b.id for a, b in zip(rows[:-1], rows[1:])))

    def test_should_returnZeroItems_when_getItemsToSend(self):
        db_conf = prepare_db()
        apply_sql_file('test/support/data/data_not_send.sql')

        dev_db = DeviceDB(
            db_config=db_conf,
            db_tablename=self.db_tablename,
            cls_item=self.item_class
        )

        rows = dev_db.get_items_to_send()

        eq_(len(rows), 0)


class TestACMPlus(BaseDBGetItemsTests):
    item_class = ACMPlusItem
    db_tablename = "acmplus"


class TestPB200(BaseDBGetItemsTests):
    item_class = WIMDA
    db_tablename = "pb200"


if __name__ == '__main__':
    unittest.main()
