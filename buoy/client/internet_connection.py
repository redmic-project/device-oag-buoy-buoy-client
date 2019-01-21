#!/usr/bin/env python3
# -*- coding: utf-8 -*- pyversions=3.3+

import logging.config
import time
import os

import buoy.client.utils.argsparse as args_parse
import buoy.client.utils.config as load_config
from buoy.client.service.daemon import Daemon
from buoy.client.network.connection import is_connected_to_internet

DAEMON_NAME = 'check-dongle-connectivity'

logger = logging.getLogger(__name__)


class IsInternetConectionDaemon(Daemon):
    def __init__(self, name, config):
        Daemon.__init__(self,  daemon_name=name, daemon_config=config['service'])

        conf = config['connection']['check']

        self.time = conf['time']
        self.num_attempts = conf['num_attempts']
        self.time_between_attempts = conf['time_between_attempts']
        self.ip = conf['ip']
        self.start_timeout = conf['start_timeout']
        self.path_reboot_files = config['service']['path_reboot_files']

    def run(self):
        first_loop = True
        while self.is_active():
            if not is_connected_to_internet(ip=self.ip, max_attempts=self.num_attempts,
                                            time_between_attempts=self.time_between_attempts):
                self.error()
            else:
                if first_loop:
                    self.delete_file_lifecycle()
                    first_loop = False

                time.sleep(self.time)

    '''
    Elimina los ficheros creados, cuando no se tiene conexión. Esto solo
    ocurre cuando se obtiene conexión a internet.    
    '''
    def delete_file_lifecycle(self):
        for file in os.listdir(self.path_reboot_files):
            logger.info("Delete file " + file)
            os.remove(os.path.join(self.path_reboot_files, file))


def run(config: str, config_log_file: str):
    logging.config.dictConfig(load_config.load_config_logger(path_config=config_log_file))
    buoy_config = load_config.load_config(path_config=config)

    daemon = IsInternetConectionDaemon(name=DAEMON_NAME, config=buoy_config)
    daemon.start()


def main():
    args = args_parse.parse_args()
    run(config=args.config_file, config_log_file=args.config_log_file)


if __name__ == "__main__":
    main()
