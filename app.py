import asyncio
from wyzeapy import Wyzeapy
import time

import mqtt as m

from dotenv import dotenv_values

secrets = dotenv_values(".env")


async def async_main():
    client = await Wyzeapy.create()
    await client.login(
        email=secrets["WYZE_EMAIL"],
        password=secrets["WYZE_PASSWORD"],
        api_key=secrets["WYZE_API_KEY"],
        key_id=secrets["WYZE_API_KEY_ID"],
    )

    camera_service = await client.camera_service
    cameras = await camera_service.get_cameras()

    floodlight_cam = next(
        camera for camera in cameras if camera.nickname == "Floodlight"
    )

    def on_message_callback(client, userdata, message, tmp=None):
        message.payload = message.payload.decode("utf-8")
        print(
            "New Received message "
            + str(message.payload)
            + " on topic '"
            + message.topic
            + "' with QoS "
            + str(message.qos)
        )
        if message.topic == m.REQUESTED_STATE_TOPIC:
            if str(message.payload) == "true":
                print("TURNING ON")
                asyncio.create_task(camera_service.floodlight_on(floodlight_cam))
            elif str(message.payload) == "false":
                print("TURNING OFF")
                loop = asyncio.get_running_loop()
                asyncio.create_task(camera_service.floodlight_off(floodlight_cam))
            else:
                print("Unknown command received: ", str(message.payload))

    mqtt_client = m.connect(on_message_callback)

    while True:
        floodlight_cam = await camera_service.update(floodlight_cam)
        floodlight_state = floodlight_cam.floodlight
        print("Writing: ", floodlight_state)
        m.write_state(mqtt_client, floodlight_state)
        await asyncio.sleep(1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main())
