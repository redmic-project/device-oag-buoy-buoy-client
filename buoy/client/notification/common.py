# -*- coding: utf-8 -*-

import logging
from enum import IntEnum

logger = logging.getLogger(__name__)


class NotificationLevel(IntEnum):
    LOW = 10
    NORMAL = 5
    HIGHT = 3
    CRITICAL = 1

