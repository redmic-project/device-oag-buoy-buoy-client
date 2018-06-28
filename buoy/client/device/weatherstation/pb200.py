# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timezone

import pynmea2

from buoy.client.device.common.base import Device, DeviceReader
from buoy.client.device.common.nmea0183 import WIMDA

logger = logging.getLogger(__name__)


class PB200Reader(DeviceReader):
    def __init__(self, **kwargs):
        super(PB200Reader, self).__init__(**kwargs)

    def parser(self, data):
        try:
            item = pynmea2.parse(data)
            if item.sentence_type == 'MDA':
                return WIMDA.from_nmea(datetime.now(tz=timezone.utc), item)
        except pynmea2.nmea.ParseError as e:
            logger.debug(e)


class PB200(Device):
    def __init__(self, *args, **kwargs):
        device_name = kwargs.pop('device_name', 'PB200')
        super(PB200, self).__init__(self, device_name=device_name, cls_reader=PB200Reader, *args, **kwargs)
