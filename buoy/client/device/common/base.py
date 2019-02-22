# -*- coding: utf-8 -*-

import logging
from queue import Queue, Empty, Full
from threading import Thread
from typing import List
from copy import copy

import paho.mqtt.client as mqtt
import time
from serial import Serial, SerialException

from buoy.client.device.common.database import DeviceDB
from buoy.client.device.common.exceptions import LostConnectionException, DeviceNoDetectedException, \
    ProcessDataExecption

from buoy.client.notification.common import BaseItem
from buoy.client.device.common.item import ItemQueue, Status
from buoy.client.device.common.limbo import Limbo

logger = logging.getLogger(__name__)


class BaseThread(Thread):
    def __init__(self, queue_notice: Queue, **kwargs):
        self.timeout_wait = kwargs.pop('timeout_wait', 0.2)
        super(BaseThread, self).__init__(**kwargs)
        self.active = False
        self.queue_notice = queue_notice

    def run(self):
        self.before_activity()
        self.active = True
        while self.is_active():
            self.activity()
            time.sleep(self.timeout_wait)
        self.after_activity()

    def is_active(self) -> bool:
        """
        Retorna el estado del hilo, activo o parado

        :return: Estado del hilo
        """
        return self.active

    def before_activity(self):
        pass

    def after_activity(self):
        pass

    def activity(self):
        """
        Función donde implementar el proceso a ejecutar el hilo
        :return:
        """
        pass

    def stop(self):
        """ Para el hilo """
        self.active = False
        logging.info("Stop thread %s", self.__class__.__name__)

    def error(self, exception):
        self.queue_notice.put_nowait(exception)
        self.stop()


class DeviceBaseThread(BaseThread):
    def __init__(self, device: Serial, queue_notice: Queue, **kwargs):
        super(DeviceBaseThread, self).__init__(queue_notice)
        self.device = device

    def is_active(self):
        return super().is_active() and self.device.is_open


class DeviceReader(DeviceBaseThread):
    """ Clase encargada de leer y parsear los datos que devuelve el dispositivo """

    def __init__(self, device: Serial, queue_notice: Queue, **kwargs):
        self.char_splitter = kwargs.pop('char_splitter', '\n')
        super(DeviceReader, self).__init__(device, queue_notice)
        self.buffer = ''

        self.queue_save_data = kwargs.pop('queue_save_data', None)
        if not self.queue_save_data:
            logging.info("No save data in database")
        self.queue_send_data = kwargs.pop('queue_send_data', None)
        if not self.queue_send_data:
            logging.info("No send data in real-time")

    def activity(self):
        try:
            self.read_data()
            logger.debug("Waiting data")
            if not self.is_buffer_empty():
                self.process_data()

        except (OSError, Exception) as ex:
            logger.error("Device disconnected")
            self.error(LostConnectionException(exception=ex))

    def read_data(self):
        self.buffer += self.device.read(self.device.in_waiting).decode()

    def is_buffer_empty(self):
        return self.char_splitter not in self.buffer

    def process_data(self):
        logger.debug("Proccessing data: %s", self.buffer)
        buffer = self.buffer.rsplit(self.char_splitter, 1)
        try:
            self.buffer = buffer[1].strip()
        except IndexError as ex:
            raise ProcessDataExecption(message="Proccesing data without char split", exception=ex)
        for line in self.split_by_lines(buffer[0]):
            item = self.parser(line)
            if item:
                self.put_in_queues(item)
            logger.debug("Received data - " + line)

    def split_by_lines(self, buffer: str) -> List[str]:
        lines = buffer.split(self.char_splitter)
        return [l.strip() for l in lines if len(l.strip())]

    def parser(self, data) -> BaseItem:
        pass

    def put_in_queues(self, item):
#        logger.info("Item readed from device - %s" % item)

        if self.queue_save_data and not self.queue_save_data.full():
            try:
                self.queue_save_data.put_nowait(ItemQueue(data=copy(item)))
            except Full as ex:
                logger.error("Save data queue is full", ex)

        if self.queue_send_data and not self.queue_send_data.full():
            try:
                self.queue_send_data.put_nowait(item)
            except Full as ex:
                logger.warning("Send data queue is full", ex)


class DeviceWriter(DeviceBaseThread):
    """ Clase encargada de enviar datos al dispositivo """

    def __init__(self, device: Serial, queue_write_data: Queue, queue_notice: Queue):
        super(DeviceWriter, self).__init__(device, queue_notice)
        self.queue_write_data = queue_write_data

    def activity(self):
        try:
            data = self.queue_write_data.get(timeout=self.timeout_wait)
            self.device.write(data.encode())
            logger.info("Write data in device - " + data)
            self.queue_write_data.task_done()
        except SerialException as ex:
            logger.error("Device disconnected")
            self.error(LostConnectionException(exception=ex))
        except Empty:
            pass


class ItemSaveThread(BaseThread):
    """
    Clase encargada de guardar los datos en la base de datos
    """

    def __init__(self, db: DeviceDB, queue_save_data: Queue, queue_notice: Queue):
        super(ItemSaveThread, self).__init__(queue_notice)
        self.db = db
        self.queue_save_data = queue_save_data

    def activity(self):
        try:
            item = self.queue_save_data.get(timeout=self.timeout_wait)

            if item.status == Status.NEW:
                self.save(item.data)
                # TODO Habría que tener encuenta si el item se guardó antes
            elif item.status == Status.SENT:
                self.set_sent(item.data)
                # TODO Habría que tener encuenta si el item no existe
            elif item.status == Status.FAILED:
                self.set_failed(item.data)

            self.queue_save_data.task_done()
        except Empty:
            pass

    def save(self, item):
        """ Guarda el registro en la base de datos """
        self.db.save(item)

    def set_sent(self, item):
        self.db.set_sent(item.uuid)

    def set_failed(self, item):
        self.db.set_failed(item.uuid)


class ItemInDBToSendThread(BaseThread):
    """
    Clase base encargada buscar datos en la base de datos que no han sido enviados
    """

    def __init__(self, db: DeviceDB, queue_send_data: Queue, queue_notice: Queue):
        super(ItemInDBToSendThread, self).__init__(queue_notice)

        self.db = db
        self.queue_send_data = queue_send_data
        self.queue_notice = queue_notice
        self.limit_queue = 100

    def activity(self):
        if self.queue_send_data.qsize() < self.limit_queue:
            items = self.db.get_items_to_send()
            for item in items:
                self.queue_send_data.put_nowait(item)


def loop(client):
    client.loop_start()


class MqttThread(BaseThread):
    """
    Clase base encargada de enviar los datos al servidor
    """

    def __init__(self, queue_send_data: Queue, queue_data_sent: Queue, queue_notice: Queue, **kwargs):
        super(MqttThread, self).__init__(queue_notice)

        self.queue_send_data = queue_send_data
        self.queue_data_sent = queue_data_sent
        self.queue_notice = queue_notice
        self.__connected_to_mqtt = False
        self.attemp_connect = False
        self.thread_mqtt = None

        self.client_id = kwargs.pop("client_id", "")
        self.clean_session = kwargs.pop("clean_session", True)
        self.protocol = mqtt.MQTTv311
        self.transport = kwargs.pop("transport", "tcp")

        self.broker_url = kwargs.pop("broker_url", "iot.eclipse.org")
        self.broker_port = kwargs.pop("broker_port", 1883)
        self.topic_data = kwargs.pop("topic_data", "buoy")
        self.keepalive = kwargs.pop("keepalive", 60)
        self.reconnect_delay = kwargs.pop("reconnect_delay", {"min_delay": 1, "max_delay": 120})

        self.client = mqtt.Client(client_id=self.client_id, protocol=self.protocol, clean_session=self.clean_session)

        self.limbo = Limbo()

        if "username" in kwargs:
            self.username = kwargs.pop("username", "username")
            self.password = kwargs.pop("password", None)
            self.client.username_pw_set(self.username, self.password)

        self.qos = kwargs.pop("qos", 0)

    def before_activity(self):
        self.connect_to_mqtt()

    def connect_to_mqtt(self):
        logger.info("Try to connect to broker")
        self.attemp_connect = True
        self.client.connect(host=self.broker_url, port=self.broker_port, keepalive=self.keepalive)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

        self.thread_mqtt = Thread(target=loop, args=(self.client,))
        self.thread_mqtt.start()

    def activity(self):
        if self.is_connected_to_mqtt():
            try:
                item = self.queue_send_data.get_nowait()
                self.send(item)
                self.queue_send_data.task_done()
            except Empty:
                logger.debug("No data for sending to broker")
                pass

    def is_connected_to_mqtt(self):
        return self.__connected_to_mqtt

    def send(self, item):
        """

        :param item:
        """
#        logger.info("Publish data '%s' to topic '%s'" % (self.topic_data, str(item.to_json())))
        try:
            rc = self.client.publish(self.topic_data, str(item.to_json()), qos=self.qos)
            self.limbo.add(rc.mid, item)
        except ValueError as ex:
            logger.error("Can't sent item", ex, exc_info=True)
            self.queue_data_sent.put_nowait(ItemQueue(data=item, status=Status.FAILED))
            pass

    def stop(self):
        logger.info("Disconnecting to broker")
        self.client.disconnect()

    def on_publish(self, client, userdata, mid):
        """
        Callback del método publish, si se entra aquí significa que el item fue
        enviado al broker correctamente

        :param client:
        :param userdata:
        :param mid:
        """
        if self.limbo.exists(mid):
            item = self.limbo.pop(mid)
            logger.debug("Update item in db %s", item.uuid)
            self.queue_data_sent.put_nowait(ItemQueue(data=item, status=Status.SENT))
        else:
            logger.warning("Item isn't in limbo")

    def on_connect(self, client, userdata, flags, rc):
        """
        :param client:
        :param userdata:
        :param flags:
        :param rc:
        """
        if rc == 0:
            logger.info("Connected to broker %s with client_id %s", self.broker_url, client)
            self.__connected_to_mqtt = True
            if flags["session present"]:
                logger.info("Connected to broker using existing session")
            else:
                logger.info("Connected to broker using clean session")
        else:
            self.__connected_to_mqtt = False
            if rc == 1:
                logger.error("Connection refused - incorrect protocol version")
            elif rc == 2:
                logger.error("Connection refused - invalid client identifier")
            elif rc == 3:
                logger.error("Connection refused - server unavailable")
            elif rc == 4:
                logger.error("Connection refused - bad username or password")
            elif rc == 5:
                logger.error("Connection refused - not authorised")
            else:
                logger.error("Error connected to broker")

    def on_disconnect(self, client, userdata, rc):
        """

        :param client:
        :param userdata:
        :param rc:
        """
        self.__connected_to_mqtt = False
        self.limbo.clear()
        if rc != 0:
            logger.error("Unexpected disconnection to broker")
        else:
            client.loop_stop()
            super().stop()
        logger.info("Disconnected to broker with result code %s" % str(rc))


class Device(object):
    def __init__(self, *args, **kwargs):
        self.serial_config = kwargs.pop('serial_config', None)
        self.db = kwargs.pop('db')

        self.cls_reader = kwargs.pop('cls_reader', None)
        self.cls_writer = kwargs.pop('cls_writer', None)
        self.cls_save = kwargs.pop('cls_save', ItemSaveThread)
        self.cls_send = kwargs.pop('cls_send', MqttThread)
        self.mqtt = kwargs.pop('mqtt', None)

        self.qsize_send_data = kwargs.pop('qsize_send_data', 1000)

        self.queues = {}
        self._create_queues()

        # Device
        self.name = kwargs.pop('device_name')
        self._dev_connection = None

    def _create_queues(self):
        for queue_name in ['notice', 'write_data', 'save_data', 'send_data']:
            qsize = 0
            if queue_name == 'send_data':
                qsize = self.qsize_send_data
            self.queues[queue_name] = Queue(maxsize=qsize)

    def run(self):
        try:
            self.connect()
            self._create_threads()
            self._start_threads()
            self.configure()
            self._listener_exceptions()
        except Exception as ex:
            logger.error(ex)
            raise ex

    def connect(self):
        logger.info("Connecting to device")
        try:
            self._dev_connection = Serial(**self.serial_config)
        except SerialException as ex:
            raise DeviceNoDetectedException(process=self.name, exception=ex)
        logger.info("Connected to device")

    def _create_threads(self):
        if self.cls_writer:
            self._thread_writer = self.cls_writer(device=self._dev_connection,
                                                  queue_write_data=self.queues['write_data'],
                                                  queue_notice=self.queues['notice'])
        if self.cls_reader:
            self._thread_reader = self.cls_reader(device=self._dev_connection,
                                                  queue_save_data=self.queues['save_data'],
                                                  queue_send_data=self.queues['send_data'],
                                                  queue_notice=self.queues['notice'])
        if self.cls_save:
            self._thread_save = self.cls_save(queue_save_data=self.queues['save_data'],
                                              queue_notice=self.queues['notice'],
                                              db=self.db)
        if self.cls_send:
            self._thread_send = self.cls_send(queue_send_data=self.queues['send_data'],
                                              queue_data_sent=self.queues['save_data'],
                                              queue_notice=self.queues['notice'],
                                              db=self.db, **self.mqtt)

    def _start_threads(self):
        self._run_action_threads(action='start')

    def _run_action_threads(self, action='start'):
        prefix = '_thread_'
        names = ['reader', 'writer', 'save', 'send']

        for name in names:
            field = prefix + name
            if hasattr(self, field):
                thread = getattr(self, field)
                getattr(thread, action)()

    def configure(self):
        pass

    def _listener_exceptions(self):
        while self.is_open():
            try:
                ex = self.queues['notice'].get(timeout=0.2)
                raise ex
            except Empty:
                pass

    def disconnect(self):
        logger.info("Disconnecting to device")
        self._stop_threads()
        if self.is_open():
            self._dev_connection.close()
        logger.info("Disconnected to device")

    def _stop_threads(self):
        self._run_action_threads(action='stop')

    def is_open(self):
        return self._dev_connection and self._dev_connection.is_open and self.is_active()

    def write(self, data):
        self.queues['write_data'].put_nowait(data + "\r")
