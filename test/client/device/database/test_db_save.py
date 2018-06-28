import unittest
from datetime import datetime, timezone

from nose.tools import eq_

from buoy.client.device.common.base import DeviceDB
from buoy.client.device.common.nmea0183 import WIMDA
from buoy.client.device.currentmeter.acmplus import ACMPlusItem
from test.support.function.database import *


class BaseDBTests(unittest.TestCase):
    item_class = None
    db_conf = None
    data = None
    skip_test = False

    @classmethod
    def setUpClass(cls):
        global skip_test

        if cls is BaseDBTests:
            skip_test = True
        else:
            skip_test = False

        super(BaseDBTests, cls).setUpClass()

    def setUp(self):
        """ Module level set-up called once before any tests in this file are executed. Creates a temporary database
        and sets it up """

        if skip_test:
            self.skipTest("Skip BaseTest tests, it's a base class")

        global db_conf

        db_conf = prepare_db()

    def tearDown(self):
        """ Called after all of the tests in this file have been executed to close the database connecton and destroy
        the temporary database """

        close_db()

    def test_add_item_in_db(self):

        item_to_insert = self.item_class(**self.data)

        dev_db = DeviceDB(
            db_config=db_conf,
            db_tablename=self.db_tablename,
            cls_item=self.item_class
        )

        item = dev_db.save(item_to_insert)

        rows = apply_sql_clause("""SELECT * FROM %s""" % (self.db_tablename,))

        eq_(len(rows), 1)
        row = rows[0]
        for key, value in self.data.items():
            eq_(row[key], value)

        eq_(row['id'], item.id)


class TestACMPlus(BaseDBTests):
    item_class = ACMPlusItem
    db_tablename = "acmplus"
    data = {
        'date': datetime.now(tz=timezone.utc),
        'vx': 30.3273,
        'vy': 1.0270,
        'speed': 20.1,
        'direction': 26.8,
        'water_temp': 12.3
    }


class TestPB200(BaseDBTests):
    item_class = WIMDA
    db_tablename = "pb200"
    data = {
        'date': datetime.now(tz=timezone.utc),
        'press_inch': 30.3273,
        'press_bar': 1.0270,
        'air_temp': 26.8,
        'water_temp': 20.1,
        'rel_humidity': 12.3,
        'abs_humidity': 21.0,
        'dew_point': 2.3,
        'wind_dir_true': 2.0,
        'wind_dir_magnetic': 128.7,
        'wind_knots': 134.6,
        'wind_meters': 0.3
    }


if __name__ == '__main__':
    unittest.main()
