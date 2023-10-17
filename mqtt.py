import paho.mqtt.client as mqtt
import socket
import time
from dotenv import dotenv_values

secrets = dotenv_values(".env")

REQUESTED_STATE_TOPIC = "wyze-python/floodlight/requested_state"


def on_connect(client, userdata, flags, rc):
    print("MQTT Connected with result code " + str(rc))


def on_disconnect(client, userdata, rc):
    print("MQTT disconnected with result code " + str(rc))


def connect(on_message_callback):
    # Set timeout for connection and reconnection
    socket.setdefaulttimeout(2)

    # MQTT variables, set the host IP
    host = secrets["MQTT_HOST"]
    port = 1883

    client = mqtt.Client("wyze-python")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message_callback
    client.connect(host, port)

    # MQTT Threaded loop starting
    client.loop_start()

    while not client.is_connected():
        print("Waiting to be connected")
        time.sleep(1)

    print("Connected")

    res = client.subscribe(REQUESTED_STATE_TOPIC)
    print("Subscribed to " + REQUESTED_STATE_TOPIC, res)

    return client


def write_state(client: mqtt.Client, state):
    try:
        topic = "wyze-python/floodlight/actual_state"
        ret = client.publish(topic, state)
        return ret
    except:
        print("Exception in MQTT write")
        return
