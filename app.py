import asyncio
from wyzeapy import Wyzeapy
import aiomqtt
import json
import datetime

TOPIC_STATE_REQUESTED = "wyze-python/floodlight/requested_state"
TOPIC_STATE_ACTUAL = "wyze-python/floodlight/actual_state"
TOPIC_STATE_FLOODLIGHT_CHANGE = "wyze-python/floodlight/actual_floodlight_change"

from dotenv import dotenv_values

secrets = dotenv_values(".env")


def log(message):
    print(
        datetime.datetime.strftime(datetime.datetime.now(), "%m/%d/%Y %H:%M:%S"),
        message,
    )


async def mqtt_listen(camera_service, floodlight_cam):
    async with aiomqtt.Client(secrets["MQTT_HOST"]) as client:
        async with client.messages() as messages:
            await client.subscribe(TOPIC_STATE_REQUESTED)
            async for message in messages:
                message.payload = message.payload.decode("utf-8")
                log(
                    "New Received message "
                    + message.topic.value
                    + " "
                    + message.payload
                )
                if message.topic.matches(TOPIC_STATE_REQUESTED):
                    if message.payload == "on":
                        log("TURNING ON")
                        await camera_service.floodlight_on(floodlight_cam)
                    elif message.payload == "off":
                        log("TURNING OFF")
                        await camera_service.floodlight_off(floodlight_cam)
                    else:
                        log("Unknown command received: " + message.payload)


async def async_main():
    mqtt_retry_interval = 10  # Seconds

    while True:
        try:
            mqtt_client = aiomqtt.Client(secrets["MQTT_HOST"])
            async with mqtt_client:
                async with asyncio.TaskGroup() as tg:
                    client = await Wyzeapy.create()
                    await client.login(
                        email=secrets["WYZE_EMAIL"],
                        password=secrets["WYZE_PASSWORD"],
                        api_key=secrets["WYZE_API_KEY"],
                        key_id=secrets["WYZE_API_KEY_ID"],
                    )
                    log("Connected to Wyze API")

                    camera_service = await client.camera_service
                    cameras = await camera_service.get_cameras()

                    floodlight_cam = next(
                        camera for camera in cameras if camera.nickname == "Floodlight"
                    )
                    log("Got floodlight camera")

                    tg.create_task(mqtt_listen(camera_service, floodlight_cam))

                    log("Starting main loop")
                    prev_state = False
                    while True:
                        floodlight_cam = await camera_service.update(floodlight_cam)

                        floodlight_state = "on" if floodlight_cam.floodlight else "off"

                        state = {
                            "floodlight": floodlight_state,
                            "on": floodlight_cam.on,
                            "motion": floodlight_cam.motion,
                            "last_event_ts": floodlight_cam.last_event_ts,
                            "raw": floodlight_cam.raw_dict,
                        }
                        state_json = json.dumps(state, indent=4)
                        # log(state_json)
                        await mqtt_client.publish(
                            TOPIC_STATE_ACTUAL, payload=state_json
                        )

                        if prev_state != floodlight_cam.floodlight:
                            log("State changed, now: " + floodlight_state)
                            await mqtt_client.publish(
                                TOPIC_STATE_FLOODLIGHT_CHANGE, payload=floodlight_state
                            )

                        prev_state = floodlight_cam.floodlight

                        await asyncio.sleep(10)
        except aiomqtt.MqttError:
            log(
                "Connection lost; Reconnecting in "
                + str(mqtt_retry_interval)
                + " seconds ..."
            )
            await asyncio.sleep(mqtt_retry_interval)


asyncio.run(async_main())
