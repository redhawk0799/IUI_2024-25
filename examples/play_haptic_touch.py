#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import _setup_sys_path
import datasets as ds

from teslasuit_sdk import ts_api
import teslasuit_sdk.subsystems.ts_haptic
from teslasuit_sdk.ts_mapper import TsBone2dIndex

TOUCH_DURATION_MS = 3000

def main():
    try:

        ds.load_dataset("dasgringuen/assettoCorsaGym")
        print("test8")


        """print("Initialize API")
        api = ts_api.TsApi()

        device = api.get_device_manager().get_or_wait_last_device_attached()
        player = device.haptic
        mapper = api.mapper

        print("Setup channels to play and touch parameters")
        layout = mapper.get_haptic_electric_channel_layout(device.get_mapping())
        bones = mapper.get_layout_bones(layout)
        channels = mapper.get_bone_contents(bones[TsBone2dIndex.RightUpperArm.value])
        params = player.create_touch_parameters(100, 40, 150)

        print("Create touch and play")
        playable_id = player.create_touch(params, channels, TOUCH_DURATION_MS)
        player.play_playable(playable_id)

        print("Wait until playback finished...")
        time.sleep(TOUCH_DURATION_MS / 1000)
        print("Finished")"""

    except (KeyboardInterrupt, SystemExit):
        print('\n! Received keyboard interrupt, quitting haptic touch play\n')


if __name__ == '__main__':
    main()
