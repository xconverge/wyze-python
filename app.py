import asyncio
from wyzeapy import Wyzeapy
import time
import aiomqtt

TOPIC_STATE_REQUESTED = "wyze-python/floodlight/requested_state"
TOPIC_STATE_ACTUAL = "wyze-python/floodlight/actual_state"

from dotenv import dotenv_values

secrets = dotenv_values(".env")


async def mqtt_listen(camera_service, floodlight_cam):
    async with aiomqtt.Client(secrets["MQTT_HOST"]) as client:
        async with client.messages() as messages:
            await client.subscribe(TOPIC_STATE_REQUESTED)
            async for message in messages:
                message.payload = message.payload.decode("utf-8")
                print("New Received message ", message.topic, message.payload)
                if message.topic.matches(TOPIC_STATE_REQUESTED):
                    if message.payload == "true":
                        print("TURNING ON")
                        await camera_service.floodlight_on(floodlight_cam)
                    elif message.payload == "false":
                        print("TURNING OFF")
                        await camera_service.floodlight_off(floodlight_cam)
                    else:
                        print("Unknown command received: ", message.payload)


async def async_main():
    async with aiomqtt.Client(secrets["MQTT_HOST"]) as mqtt_client:
        async with asyncio.TaskGroup() as tg:
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

            tg.create_task(mqtt_listen(camera_service, floodlight_cam))

            while True:
                floodlight_cam = await camera_service.update(floodlight_cam)
                floodlight_state = floodlight_cam.floodlight
                print("Writing: ", floodlight_state)
                await mqtt_client.publish(TOPIC_STATE_ACTUAL, payload=floodlight_state)
                await asyncio.sleep(1)


asyncio.run(async_main())
