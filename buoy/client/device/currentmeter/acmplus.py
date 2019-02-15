# -*- coding: utf-8 -*-

import logging
import re
from datetime import datetime, timezone

from buoy.client.device.common.base import DeviceReader, DeviceWriter, MqttThread, Device
from buoy.client.device.currentmeter.item import ACMPlusItem

logger = logging.getLogger(__name__)


class ACMPlusReader(DeviceReader):
    def __init__(self, **kwargs):
        super(ACMPlusReader, self).__init__(**kwargs)
        self.pattern = ("\s*(?P<vy>-?\d{1,}.\d{1,}),\s{1,}(?P<vx>-?\d{1,}.\d{1,}),\s{1,}(?P<time>\d{2}:\d{2}:\d{2})"
                        ",\s{1,}(?P<date>\d{2}-\d{2}-\d{4}),\s{1,}(?P<waterTemperature>-?\d{1,}.\d{1,}).*")

    def parser(self, data):
        result = re.match(self.pattern, data)
        if result:
            measurement = ACMPlusItem(
                date=datetime.now(tz=timezone.utc),
                vx=result.group("vx"),
                vy=result.group("vy"),
                water_temp=result.group("waterTemperature")
            )

            return measurement


class ACMPlusWriter(DeviceWriter):
    def __init__(self, **kwargs):
        super(ACMPlusWriter, self).__init__(**kwargs)


class ACMPlusSender(MqttThread):
    def __init__(self, **kwargs):
        super(MqttThread, self).__init__(**kwargs)


class ACMPlus(Device):
    def __init__(self, device_name='ACMPlus', **kwargs):
        super(ACMPlus, self).__init__(device_name=device_name, cls_reader=ACMPlusReader, cls_writer=ACMPlusWriter,
                                      cls_sender=ACMPlusSender, **kwargs)

    def configure(self):
        self.write("MODE")
