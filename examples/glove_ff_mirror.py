#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import ctypes
import _setup_sys_path

from teslasuit_sdk import ts_api
from teslasuit_sdk import ts_types
from teslasuit_sdk.ts_mapper import TsBone2dIndex
from teslasuit_sdk.subsystems import ts_magnetic_encoder

GLOVE_COUNT = 2
DEFAULT_HARDNESS = 100

def main():
    is_streaming = False
    try:
        print("Initialize API")
        api = ts_api.TsApi()
        
        devices = api.get_device_manager().wait_for_device_to_connect(GLOVE_COUNT)

        glove_a = api.get_device_manager().devices[0]
        glove_b = api.get_device_manager().devices[1]
        print("Detecting connected devices")
        if glove_a.type != ts_types.TsDeviceType.Glove:
            print("First connected device was not detected as Glove. Please connect two gloves and  start application again.")
            return
        if glove_b.type != ts_types.TsDeviceType.Glove:
            print("Second connected device was not detected as Glove. Please connect two gloves and     start application again.")
            return
        if glove_a.side == ts_types.TsDeviceSide.Undefined or glove_b.side ==   ts_types.TsDeviceSide.Undefined:
            print("Glove side was not detected. Please connect two gloves with latest firmware and  start application again.")
            return
        print("Glove A:", glove_a.get_device_ssid(), "| Glove B:", glove_b.get_device_ssid())
        encoder_a = glove_a.magnetic_encoder
        encoder_b = glove_b.magnetic_encoder

        ff_controls = encoder_b.get_default_ff_controls_struct()
        def on_data_received(positions):
            i = 0
            for bone_index in positions.fingers.keys():
                ff_controls[i].angle = ctypes.c_float(positions.fingers[bone_index].flexion_angle)
                ff_controls[i].hardness_percent = DEFAULT_HARDNESS
                ff_controls[i].lock_direction = ts_magnetic_encoder.TsForceFeedbackLockDirection.Both.value
                i = i + 1
            encoder_b.ts_force_feedback_enable(ff_controls)            
        print("Start magnetic encoder streaming")
        encoder_a.set_data_update_callback(on_data_received)
        encoder_a.start_me_streaming()
        is_streaming = True
        while True:
            time.sleep(0.001)

        print("Finished")

    except (KeyboardInterrupt, SystemExit):
        print('\n! Received keyboard interrupt, quitting glove ff mirror\n')

    if is_streaming:
        print("Stop magnetic encoder streaming")
        encoder_a.stop_me_streaming()
        time.sleep(0.5)
        print("Release force feedback")
        encoder_b.ts_force_feedback_disable(encoder_b.get_bone_indexes())


def single():
    is_streaming = False
    try:
        print("Initialize API")
        api = ts_api.TsApi()
        api.get_device_manager().wait_for_device_to_connect()
        glove = api.get_device_manager().devices[0]
        print("Detecting connected device")
        if glove.type != ts_types.TsDeviceType.Glove:
            print("Connected device was not detected as Glove. Please connect glove and start   application again.")
            return
        if glove.side == ts_types.TsDeviceSide.Undefined:
            print("Glove side was not detected. Please connect glove with latest firmware and start     application again.")
            return
        print("Glove:", glove.get_device_ssid())
        encoder = glove.magnetic_encoder

        ff_controls = [ts_magnetic_encoder.TsForceFeedbackConfig()]
        bone_index_from = encoder.get_bone_indexes()[1]
        bone_index_to = encoder.get_bone_indexes()[2]
        print('From to:', bone_index_from, bone_index_to)
        def on_data_received(positions):
            ff_controls[0].bone_index = bone_index_to.value
            ff_controls[0].angle = ctypes.c_float(positions.fingers[bone_index_from].flexion_angle)
            ff_controls[0].hardness_percent = DEFAULT_HARDNESS
            ff_controls[0].lock_direction = ts_magnetic_encoder.TsForceFeedbackLockDirection.Both.value
            encoder.ts_force_feedback_enable(ff_controls)            
        print("Start magnetic encoder streaing")
        encoder.set_data_update_callback(on_data_received)
        encoder.start_me_streaming()
        is_streaming = True
        while True:
            time.sleep(0.001)

        print("Finished")

    except (KeyboardInterrupt, SystemExit):
        print('\n! Received keyboard interrupt, quitting glove ff mirror\n')

    if is_streaming:
        print("Stop magnetic encoder streaming")
        encoder.stop_me_streaming()
        time.sleep(0.5)
        print("Release force feedback")
        encoder.ts_force_feedback_disable(encoder.get_bone_indexes())


main()
#single()
