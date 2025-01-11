#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import _setup_sys_path

from teslasuit_sdk import ts_api
from teslasuit_sdk.ts_mapper import TsBone2dIndex
from teslasuit_sdk.subsystems.ts_magnetic_encoder import (TsForceFeedbackLockDirection, 
    TsForceFeedbackConfig)

def main():
    try:
        print("Initialize API")
        api = ts_api.TsApi()
        
        device = api.get_device_manager().get_or_wait_last_device_attached()

        encoder = device.magnetic_encoder

        print("Set force feedback angle")
        ff_config = [TsForceFeedbackConfig()]
        ff_config[0].bone_index = TsBone2dIndex.RightThumbProximal.value
        ff_config[0].angle = 45
        ff_config[0].hardness_percent = 100
        ff_config[0].lock_direction = TsForceFeedbackLockDirection.Both.value
        encoder.ts_force_feedback_enable(ff_config)
        time.sleep(10)
        print("Release force feedback")
        encoder.ts_force_feedback_disable([TsBone2dIndex.RightThumbProximal.value])
        print("Finished")

    except (KeyboardInterrupt, SystemExit):
        print('\n! Received keyboard interrupt, quitting glove forcefeedback\n')

main()
