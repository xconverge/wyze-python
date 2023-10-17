import asyncio
from wyzeapy import Wyzeapy
import aiomqtt
import json

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
            print("Connected to Wyze API")

            camera_service = await client.camera_service
            cameras = await camera_service.get_cameras()

            floodlight_cam = next(
                camera for camera in cameras if camera.nickname == "Floodlight"
            )
            print("Got floodlight camera")

            tg.create_task(mqtt_listen(camera_service, floodlight_cam))

            print("Starting main loop")
            while True:
                floodlight_cam = await camera_service.update(floodlight_cam)

                state = {
                    "floodlight": floodlight_cam.floodlight,
                    "on": floodlight_cam.on,
                    "motion": floodlight_cam.motion,
                    "last_event_ts": floodlight_cam.last_event_ts,
                    "last_event": floodlight_cam.last_event,
                    "raw": floodlight_cam.raw_dict,
                }
                state_json = json.dumps(state, indent=4)

                # print(state_json)

                await mqtt_client.publish(TOPIC_STATE_ACTUAL, payload=state_json)
                await asyncio.sleep(1)


asyncio.run(async_main())
