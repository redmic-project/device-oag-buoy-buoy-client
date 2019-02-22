import json
import unittest
from datetime import datetime, timezone

from buoy.client.device.common.item import DataEncoder
from buoy.client.device.common.nmea0183 import WIMDA


class TestItem(unittest.TestCase):
    def setUp(self):
        pass

    def test_encoder_to_json(self):
        now = datetime.now(tz=timezone.utc)
        now.replace(microsecond=0)
        now.isoformat(timespec='milliseconds')
        data = {
            'date': datetime.now(tz=timezone.utc),
            'barometric_pressure_inch': 30.327,
            'barometric_pressure_bar': 1.027,
            'air_temperature': 26.8,
            'water_temperature': 20.1,
            'rel_humidity': 12.3,
            'abs_humidity': 21.0,
            'dew_point': 2.3,
            'wind_dir_true': 2.0,
            'wind_dir_magnetic': 128.7,
            'wind_knots': 134.6,
            'wind_meters': 0.3
        }

        item = WIMDA(**data)
        json_to_send = json.dumps(item, sort_keys=True, cls=DataEncoder)

        # TODO Corregir test


# eq_(json_to_send['date'], now)


if __name__ == '__main__':
    unittest.main()
