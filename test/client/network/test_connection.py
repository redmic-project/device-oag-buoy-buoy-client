import unittest
from subprocess import CalledProcessError
from unittest.mock import patch

from nose.tools import eq_

from buoy.client.network import connection


class TestConnectionInternet(unittest.TestCase):
    def setUp(self):
        pass

    @patch.object(connection, 'check_call', side_effect=CalledProcessError(1, 'ping'))
    def test_internet_conection_fail(self, mock_method):
        max_attempts = 5

        eq_(False, connection.is_connected_to_internet(max_attempts=max_attempts, time_between_attempts=1))
        eq_(mock_method.call_count, max_attempts)

    @patch.object(connection, 'check_call', side_effect=[CalledProcessError(1, 'ping'), CalledProcessError(1, 'ping'),
                                                         CalledProcessError(1, 'ping'), CalledProcessError(1, 'ping'),
                                                         CalledProcessError(1, 'ping'), CalledProcessError(1, 'ping'),
                                                         CalledProcessError(1, 'ping'), CalledProcessError(1, 'ping'),
                                                         CalledProcessError(1, 'ping'), 0])
    def test_internet_conection_return_ok_after_various_fails(self, mock_method):
        max_attempts = 10

        eq_(True, connection.is_connected_to_internet(max_attempts=max_attempts, time_between_attempts=1))
        eq_(mock_method.call_count, max_attempts)


if __name__ == '__main__':
    unittest.main()
