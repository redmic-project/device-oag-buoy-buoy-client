#!/usr/bin/env python3
# -*- coding: utf-8 -*- pyversions=3.3+

import logging.config
import os
import datetime
import buoy.lib.utils.argsparse as args_parse
import buoy.lib.utils.config as load_config

DAEMON_NAME = 'reboot-computer'


def run(config_buoy: str, config_log_file: str):
    logging.config.dictConfig(load_config.load_config_logger(DAEMON_NAME, path_config=config_log_file))
    config = load_config.load_config(path_config=config_buoy)
    path_reboot_files = config['service']['path_reboot_files']

    with open(os.path.join(path_reboot_files, 'reboot'), 'w') as f:
        date = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.utcnow())
        f.write(date)

    os.system('systemctl reboot')


def main():
    args = args_parse.parse_args()
    run(config_buoy=args.config_file, config_log_file=args.config_log_file)


if __name__ == "__main__":
    main()
