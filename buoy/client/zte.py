#!/usr/bin/env python3
# -*- coding: utf-8 -*- pyversions=3.3+

import logging.config
import os
import datetime
import subprocess

import buoy.lib.utils.argsparse as args_parse
import buoy.lib.utils.config as load_config
from vodem.api import connect_network, disconnect_network

DAEMON_NAME = 'ZTE823'


def is_need_reboot(path_reboot_files: str):
    exists_zte_reboot_file = os.path.isfile(os.path.join(path_reboot_files, 'zte_reboot'))
    exists_reboot_file = os.path.isfile(os.path.join(path_reboot_files, 'reboot'))

    return not exists_zte_reboot_file or exists_reboot_file


def run_zte_reboot(config_buoy: str, config_log_file: str):
    logging.config.dictConfig(load_config.load_config_logger(path_config=config_log_file))
    config = load_config.load_config(path_config=config_buoy)
    path_reboot_files = config['service']['path_reboot_files']

    if is_need_reboot(path_reboot_files):
        if not os.path.exists(path_reboot_files):
            os.makedirs(path_reboot_files)

        with open(os.path.join(path_reboot_files, 'zte_reboot'), 'w') as f:
            date = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.utcnow())
            f.write(date)

        subprocess.check_call('reboot-dongle')
    else:
        os._exit(os.EX_OSERR)


def run_zte_connect(config_log_file: str):
    logging.config.dictConfig(load_config.load_config_logger(path_config=config_log_file))

    connect_network()


def run_zte_disconnect(config_log_file: str):
    logging.config.dictConfig(load_config.load_config_logger(path_config=config_log_file))

    disconnect_network()


def zte_reboot():
    args = args_parse.parse_args()
    run_zte_reboot(config_buoy=args.config_file, config_log_file=args.config_log_file)


def zte_connect():
    args = args_parse.parse_args()
    run_zte_connect(config_log_file=args.config_log_file)


def zte_disconnect():
    args = args_parse.parse_args()
    run_zte_disconnect(config_log_file=args.config_log_file)
