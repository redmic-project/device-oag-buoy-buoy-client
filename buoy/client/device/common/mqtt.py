import collections
import errno
import os
import platform
import select
import socket

from paho.mqtt.client import *

try:
    import ssl
except ImportError:
    ssl = None


class MqttClient(Client):
    def __init__(self, client_id="", clean_session=True, userdata=None,
                 protocol=MQTTv311, transport="tcp"):
        super(MqttClient, self).__init__(client_id=client_id, clean_session=clean_session,
                                         userdata=userdata, protocol=protocol, transport=transport)

    def publish(self, topic, payload=None, qos=0, retain=False, mid=None):
        """Publish a message on a topic.

        This causes a message to be sent to the broker and subsequently from
        the broker to any clients subscribing to matching topics.

        topic: The topic that the message should be published on.
        payload: The actual message to send. If not given, or set to None a
        zero length message will be used. Passing an int or float will result
        in the payload being converted to a string representing that number. If
        you wish to send a true int/float, use struct.pack() to create the
        payload you require.
        qos: The quality of service level to use.
        retain: If set to true, the message will be set as the "last known
        good"/retained message for the topic.

        Returns a MQTTMessageInfo class, which can be used to determine whether
        the message has been delivered (using info.is_published()) or to block
        waiting for the message to be delivered (info.wait_for_publish()). The
        message ID and return code of the publish() call can be found at
        info.mid and info.rc.

        For backwards compatibility, the MQTTMessageInfo class is iterable so
        the old construct of (rc, mid) = client.publish(...) is still valid.

        rc is MQTT_ERR_SUCCESS to indicate success or MQTT_ERR_NO_CONN if the
        client is not currently connected.  mid is the message ID for the
        publish request. The mid value can be used to track the publish request
        by checking against the mid argument in the on_publish() callback if it
        is defined.

        A ValueError will be raised if topic is None, has zero length or is
        invalid (contains a wildcard), if qos is not one of 0, 1 or 2, or if
        the length of the payload is greater than 268435455 bytes."""
        if topic is None or len(topic) == 0:
            raise ValueError('Invalid topic.')

        topic = topic.encode('utf-8')

        if self._topic_wildcard_len_check(topic) != MQTT_ERR_SUCCESS:
            raise ValueError('Publish topic cannot contain wildcards.')

        if qos < 0 or qos > 2:
            raise ValueError('Invalid QoS level.')

        if isinstance(payload, unicode):
            local_payload = payload.encode('utf-8')
        elif isinstance(payload, (bytes, bytearray)):
            local_payload = payload
        elif isinstance(payload, (int, float)):
            local_payload = str(payload).encode('ascii')
        elif payload is None:
            local_payload = b''
        else:
            raise TypeError('payload must be a string, bytearray, int, float or None.')

        if len(local_payload) > 268435455:
            raise ValueError('Payload too large.')

        if mid:
            local_mid = mid
        else:
            local_mid = self._mid_generate()

        if qos == 0:
            info = MQTTMessageInfo(local_mid)
            rc = self._send_publish(local_mid, topic, local_payload, qos, retain, False, info)
            info.rc = rc
            return info
        else:
            message = MQTTMessage(local_mid, topic)
            message.timestamp = time_func()
            message.payload = local_payload
            message.qos = qos
            message.retain = retain
            message.dup = False

            with self._out_message_mutex:
                if self._max_queued_messages > 0 and len(self._out_messages) >= self._max_queued_messages:
                    message.info.rc = MQTT_ERR_QUEUE_SIZE
                    return message.info

                if local_mid in self._out_messages:
                    message.info.rc = MQTT_ERR_QUEUE_SIZE
                    return message.info

                self._out_messages[message.mid] = message
                if self._max_inflight_messages == 0 or self._inflight_messages < self._max_inflight_messages:
                    self._inflight_messages += 1
                    if qos == 1:
                        message.state = mqtt_ms_wait_for_puback
                    elif qos == 2:
                        message.state = mqtt_ms_wait_for_pubrec

                    rc = self._send_publish(message.mid, topic, message.payload, message.qos, message.retain,
                                            message.dup)

                    # remove from inflight messages so it will be send after a connection is made
                    if rc is MQTT_ERR_NO_CONN:
                        self._inflight_messages -= 1
                        message.state = mqtt_ms_publish

                    message.info.rc = rc
                    return message.info
                else:
                    message.state = mqtt_ms_queued
                    message.info.rc = MQTT_ERR_SUCCESS
                    return message.info
