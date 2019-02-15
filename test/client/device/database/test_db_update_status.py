import unittest

from nose.tools import eq_, ok_

from buoy.client.device.common.base import DeviceDB
from buoy.client.device.common.nmea0183 import WIMDA
from buoy.client.device.currentmeter.acmplus import ACMPlusItem
from test.support.function.database import *


class BaseDBUpdateStatusTests(unittest.TestCase):
    item_class = None
    db_tablename = None
    db_conf = None
    skip_test = False

    @classmethod
    def setUpClass(cls):
        global skip_test

        if cls is BaseDBUpdateStatusTests:
            skip_test = True
        else:
            skip_test = False

        super(BaseDBUpdateStatusTests, cls).setUpClass()

    def setUp(self):
        """ Module level set-up called once before any tests in this file are executed. Creates a temporary database
        and sets it up """

        if skip_test:
            self.skipTest("Skip BaseTest tests, it's a base class")

        global db_conf

        db_conf = prepare_db()
        apply_sql_file('test/support/data/data_example.sql')

    def tearDown(self):
        """ Called after all of the tests in this file have been executed to close the database connecton and destroy
        the temporary database """

        close_db()

    def test_update_status_items_in_db(self):

        dev_db = DeviceDB(
            db_config=db_conf,
            db_tablename=self.db_tablename,
            cls_item=self.item_class
        )

        sql_clause = """SELECT * FROM %s ORDER BY date""" % (self.db_tablename,)
        before_rows = apply_sql_clause(sql_clause)

        uuids = list()
        for row in before_rows:
            uuids.append(row['uuid'])
        dev_db.update_status(uuids)

        after_rows = apply_sql_clause(sql_clause)

        for idx, aft_row in enumerate(after_rows):
            eq_(aft_row['sended'], True)
            ok_(aft_row['uuid'] == before_rows[idx]['uuid'])
            ok_(aft_row['num_attempts'] > before_rows[idx]['num_attempts'])


class TestACMPlus(BaseDBUpdateStatusTests):
    item_class = ACMPlusItem
    db_tablename = "acmplus"


class TestPB200(BaseDBUpdateStatusTests):
    item_class = WIMDA
    db_tablename = "pb200"


if __name__ == '__main__':
    unittest.main()
