import unittest
from os import EX_OSERR, EX_OK
from unittest.mock import patch

from buoy.client.internet_connection import IsInternetConectionDaemon


class IsInternetConectionDaemonTest(unittest.TestCase):
    def setUp(self):
        config = {
            'service': {
                'path_pidfile': './test/logs/',
                'path_reboot_files': './test/logs/lifecycle'
            },
            'connection': {
                'check': {
                    'start_timeout': 0,
                    'time': 2,
                    'num_attempts': 1,
                    'time_between_attempts': 1,
                    'ip': '8.8.8.8'
                }
            }
        }
        self.daemon = IsInternetConectionDaemon(name="Internet", config=config)

    @patch('buoy.client.internet_connection.is_connected_to_internet', side_effect=[False])
    def test_shouldReturnExitCodeError_when_internetIsDown(self, mock_check_internet):
        with self.assertRaises(SystemExit) as cm:
            self.daemon.start()

        self.assertEqual(cm.exception.code, EX_OSERR)

    @patch('buoy.client.internet_connection.is_connected_to_internet', side_effect=[True, True])
    @patch.object(IsInternetConectionDaemon, 'is_active', side_effect=[True, True, False, True])
    @patch.object(IsInternetConectionDaemon, 'delete_file_lifecycle', return_value=None)
    def test_shouldReturnExitCodeOK_when_internetIsUp(self, mock_check_internet, mock_is_active, mock_del_file):
        with self.assertRaises(SystemExit) as cm:
            self.daemon.start()

        self.assertEqual(cm.exception.code, EX_OK)


if __name__ == '__main__':
    unittest.main()
