# -*- coding: utf-8 -*-

import logging
from queue import PriorityQueue

from buoy.client.notification.common import NoticeBase

logger = logging.getLogger(__name__)


class NoticePriorityQueue(PriorityQueue):
    def __init__(self, **kwargs):
        super(NoticePriorityQueue, self).__init__(**kwargs)

    def put_nowait(self, item: NoticeBase):
        super(NoticePriorityQueue, self).put_nowait(item)

    def put(self, item: NoticeBase, block=True, timeout=None):
        super(NoticePriorityQueue, self).put((item.level, item), block, timeout)

    def get(self, block=True, timeout=None):
        _, item = super(NoticePriorityQueue, self).get(block=block, timeout=timeout)
        return item

    def join(self):
        super(NoticePriorityQueue, self).join()
