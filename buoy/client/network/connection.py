# -*- coding: utf-8 -*-

import logging
from subprocess import DEVNULL, STDOUT, check_call, CalledProcessError

import time

logger = logging.getLogger(__name__)


def is_connected_to_internet(max_attempts=3, time_between_attempts=2, ip='8.8.8.8', timeout='3') -> bool:
    logger.info("Check connection internet status")
    connected = False
    for i in range(max_attempts):
        try:
            check_call(['/bin/ping', '-c', '1', ip, '-W', timeout], stdout=DEVNULL, stderr=STDOUT)
            connected = True
            break
        except CalledProcessError:
            if i < max_attempts:
                time.sleep(time_between_attempts)

    logger.info("Connection internet status: %s", connected)
    return connected
