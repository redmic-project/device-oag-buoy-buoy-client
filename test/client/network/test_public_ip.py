import random
import unittest
from os.path import getsize, isfile
from unittest.mock import MagicMock, patch

from nose.tools import ok_, eq_

from buoy.client.network import ip
from buoy.client.utils.config import load_config


def random_ip():
    return '.'.join('%s' % random.randint(0, 255) for i in range(4))


class MockResponse:
    def __init__(self, **kwargs):
        self.content = str.encode(kwargs.pop('content', ""))
        self.status_code = kwargs.pop('status_code', 404)


class TestMyIP(unittest.TestCase):
    def setUp(self):
        self.config = load_config('./test/support/config/ip.yaml')
        self.my_ip = ip.PublicIP(**self.config['IP'])

    def test_change_public_ip_the_property_has_changed_is_equal_true(self):
        ip.get_public_ip = MagicMock(return_value=random_ip())

        ok_(self.my_ip.has_changed)

    @patch.object(ip.PublicIP, '_save')
    def test_should_call_once_save_method_when_has_changed_public_ip(self, mock_method):
        ip_expected = random_ip()
        ip.get_public_ip = MagicMock(return_value=ip_expected)

        ok_(self.my_ip.has_changed)
        mock_method.assert_called_once_with(ip=ip_expected)

    @patch.object(ip, 'get_public_ip', return_value=random_ip())
    def test_should_save_ip_in_file_cip_when_has_changed_public_ip(self, mock_method):
        ok_(self.my_ip.has_changed)

        with open(self.config['IP']['file_current_ip'], 'r') as f:
            saved_ip = f.read()
            eq_(mock_method.return_value, saved_ip)

    @patch.object(ip, 'get_public_ip', side_effect=ip.NoIPException)
    def test_should_write_emtpy_file_cip_when_no_internet_connection(self, mock_method):
        ok_(self.my_ip.has_changed)
        ok_(isfile(self.config['IP']['file_current_ip']))
        eq_(getsize(self.config['IP']['file_current_ip']), 0)


if __name__ == '__main__':
    unittest.main()
