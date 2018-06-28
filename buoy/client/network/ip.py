# -*- coding: utf-8 -*-

import ipaddress
import logging
from os import path

from requests import get, exceptions

logger = logging.getLogger(__name__)


class NoIPException(Exception):
    pass


def get_public_ip(**kwargs):
    services = kwargs.pop('services', ['http://icanhazip.com', 'http://ipv4bot.whatismyipaddress.com',
                                       'https://api.ipify1.org', 'http://ip.42.pl/raw'])
    ip = None
    for service in services:
        try:
            data = get(service).content.decode()
            ip = ipaddress.ip_address(data)
            break
        except exceptions.RequestException:
            logger.info("No connection to internet")
        except ValueError:
            logger.info("Return error IP")

    if ip is None:
        raise NoIPException()

    logger.info("Service: {0} - Public ip {1}".format(service, ip))
    return str(ip)


class NoConnectionInternetException(Exception):
    pass


class PublicIP(object):
    def __init__(self, **kwargs):
        self._ip = None
        self._has_changed = False

        self._my_public_services = kwargs.pop('my_public_ip_services')
        self._file_current_ip = kwargs.pop('file_current_ip')

        self._load_current_ip()

    def _load_current_ip(self):
        if path.exists(self._file_current_ip):
            with open(self._file_current_ip, 'r') as file:
                ip = file.readline()
                try:
                    if ipaddress.ip_address(ip):
                        self._ip = ip
                except ValueError:
                    pass
                finally:
                    file.close()

            logger.info("Current IP: %s" % (self._ip,))
        else:
            logger.info("No exists file")

    @property
    def ip(self):

        return self._ip

    @ip.setter
    def ip(self, value):
        if self._ip != value:
            self._ip = value
            self._has_changed = True
            self._save(ip=value)

    @property
    def has_changed(self):
        try:
            self.ip = get_public_ip(services=self._my_public_services)
        except NoIPException:
            logger.error("No ip")
            self.ip = None

        return self._has_changed

    def _save(self, ip):
        with open(self._file_current_ip, 'w') as file:
            if ip:
                file.write(ip)
            file.close()
