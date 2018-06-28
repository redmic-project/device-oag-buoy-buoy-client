import unittest
from test.support.function.base_device_tests import BaseDeviceTest
from buoy.client.current_meter import CurrentMeterDaemon

config_buoy_file = "test/support/config/buoy.yaml"
config_log_file = "test/support/config/logging.yaml"


class TestDeviceCurrentMeter(BaseDeviceTest):
    device_class = CurrentMeterDaemon
    DEVICE_NAME = "ACMPlus"
    __test__ = True


if __name__ == '__main__':
    unittest.main()
