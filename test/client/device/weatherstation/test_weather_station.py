import unittest

from test.support.function.base_device_tests import BaseDeviceTest
from buoy.client.weather_station import WeatherStationDaemon


config_buoy_file = "test/support/config/buoy.yaml"
config_log_file = "test/support/config/logging.yaml"


class TestDeviceWeatherStation(BaseDeviceTest):
    device_class = WeatherStationDaemon
    DEVICE_NAME = 'PB200'
    __test__ = True


if __name__ == '__main__':
    unittest.main()
