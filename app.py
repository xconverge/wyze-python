import asyncio
from wyzeapy import Wyzeapy
import time

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

    print(floodlight_cam)

    # await camera_service.floodlight_on(floodlight_cam)
    # time.sleep(1)
    # floodlight_cam = await camera_service.update(floodlight_cam)
    # time.sleep(1)
    # print(floodlight_cam.floodlight)

    # await camera_service.floodlight_off(floodlight_cam)
    # time.sleep(1)
    # floodlight_cam = await camera_service.update(floodlight_cam)
    # time.sleep(1)
    # print(floodlight_cam.floodlight)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main())
