#!/usr/bin/env python3.6
# -*- coding: utf-8 -*- pyversions=3.6+

import logging.config

import buoy.client.utils.argsparse as args_parse
import buoy.client.utils.config as load_config

from buoy.client.device.common.database import DeviceDB
from buoy.client.device.currentmeter.acmplus import ACMPlus, ACMPlusItem
from buoy.client.service.daemon import Daemon, get_config

DEVICE_NAME = 'ACMPlus'
DAEMON_NAME = 'current-meter'

logger = logging.getLogger(__name__)


class CurrentMeterDaemon(ACMPlus, Daemon):
    def __init__(self, name, buoy_config):
        serial_config, mqtt_config, db_config, service_config = get_config(name, buoy_config=buoy_config)
        db = DeviceDB(db_config=db_config, db_tablename=name, cls_item=ACMPlusItem)

        Daemon.__init__(self, daemon_name=DAEMON_NAME, daemon_config=service_config)
        ACMPlus.__init__(self, serial_config=serial_config, db=db, mqtt=mqtt_config)

    def before_stop(self):
        self.disconnect()


def run(config_buoy: str, config_log_file: str):
    logging.config.dictConfig(load_config.load_config_logger(path_config=config_log_file))
    buoy_config = load_config.load_config(path_config=config_buoy)

    daemon = CurrentMeterDaemon(name=DEVICE_NAME, buoy_config=buoy_config)
    daemon.start()


def main():
    args = args_parse.parse_args()
    run(config_buoy=args.config_file, config_log_file=args.config_log_file)


if __name__ == "__main__":
    main()
