import threading
import unittest
from os import EX_OK

import time

import buoy.client.utils.config as load_config
from buoy.client.current_meter import CurrentMeterDaemon
from buoy.client.weather_station import WeatherStationDaemon

config_buoy_file = "test/support/config/buoy.yaml"
config_ip_file = "test/support/config/ip.yaml"
config_log_file = "test/support/config/logging.yaml"


class TestConsoleCLI(unittest.TestCase):
    def setUp(self):
        self.buoy_config = load_config.load_config(path_config=config_buoy_file)

#    @unittest.skip
    def test_run_weather_station(self):
        daemon = WeatherStationDaemon(name="PB200", buoy_config=self.buoy_config)
        t = threading.Thread(target=daemon.start)
        t.start()
#        time.sleep(10000)
#        with self.assertRaises(SystemExit) as cm:
#            daemon.stop()

#        self.assertEqual(cm.exception.code, EX_OK)

    @unittest.skip
    def test_run_current_meter(self):
        daemon = CurrentMeterDaemon(name="ACMPlus", buoy_config=self.buoy_config)
        t = threading.Thread(target=daemon.start)
        t.start()
        time.sleep(10000)
        with self.assertRaises(SystemExit) as cm:
            daemon.stop()

        self.assertEqual(cm.exception.code, EX_OK)

    '''def test_run_zte_reboot(self):
        zte_reboot(config_buoy=config_buoy_file, config_log_file=config_log_file)

    
    def test_run_zte_disconnect(self):
        zte_disconnect(config_log_file=config_log_file)
    


    def test_run_zte_connect(self):
        zte_connect(config_buoy=config_buoy_file, config_log_file=config_log_file)


    def test_run_update_public_ip(self):
        update_public_ip(config_file=config_ip_file, config_log_file=config_log_file)



        

        


    def test_run_public_ip(self):
        public_ip()

    def test_run_is_connected_to_internet(self):
        connected_to_internet(config=config_buoy_file, config_log_file=config_log_file)





'''


if __name__ == '__main__':
    unittest.main()
