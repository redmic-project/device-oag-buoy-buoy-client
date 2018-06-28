import unittest
from unittest.mock import patch

from nose.tools import eq_

from buoy.client.network import ip


class MockResponse:
    def __init__(self, **kwargs):
        self.content = str.encode(kwargs.pop('content', ""))
        self.status_code = kwargs.pop('status_code', 404)


class TestPublicIP(unittest.TestCase):
    def setUp(self):
        self.services = ['http://icanhazip.com', 'http://ipv4bot.whatismyipaddress.com',
                         'https://api.ipify1.org', 'http://ip.42.pl/raw']

    @patch.object(ip, 'get')
    def test_get_public_ip_return_ip_in_last_service(self, mock_method):
        service_ok = self.services[-1]
        max_attempts = len(self.services)
        ip_expected = "128.128.128.128"

        def mocked_requests_get(*args, **kwargs):
            mock_resp = MockResponse()
            if args[0] == service_ok:
                mock_resp = MockResponse(content=ip_expected, status_code=200)

            return mock_resp

        mock_method.side_effect = mocked_requests_get

        eq_(ip_expected, ip.get_public_ip(services=self.services))
        eq_(mock_method.call_count, max_attempts)

    @patch.object(ip, 'get')
    def test_get_public_ip_return_ip_in_first_service(self, mock_method):
        service_ok = self.services[0]
        max_attempts = 1
        ip_expected = "128.128.128.128"

        def mocked_requests_get(*args, **kwargs):
            mock_resp = MockResponse()
            if args[0] == service_ok:
                mock_resp = MockResponse(content=ip_expected, status_code=200)

            return mock_resp

        mock_method.side_effect = mocked_requests_get

        eq_(ip_expected, ip.get_public_ip(services=self.services))
        eq_(mock_method.call_count, max_attempts)

    @patch.object(ip, 'get')
    def test_get_public_ip_return_exception(self, mock_method):
        max_attempts = len(self.services)

        def mocked_requests_get(*args, **kwargs):
            return MockResponse()

        mock_method.side_effect = mocked_requests_get

        self.assertRaises(ip.NoIPException, ip.get_public_ip, services=self.services)
        eq_(mock_method.call_count, max_attempts)


if __name__ == '__main__':
    unittest.main()
