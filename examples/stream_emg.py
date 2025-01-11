#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import _setup_sys_path

from teslasuit_sdk import ts_api

def main():
    is_streaming = False
    try:
        print("Initialize API")
        api = ts_api.TsApi()

        device = api.get_device_manager().get_or_wait_last_device_attached()
        emg = device.emg

        desired_fps = 60
        period_in_ms = 1. / desired_fps
        frames_to_stream = 10

        # To configure streaming properties
        # emg.set_options(lower_bandwidth, upper_bandwidth, sampling_freq, sample_size)

        print("Start streaming...")
        emg.start_streaming()
        is_streaming = True

        while frames_to_stream:
            time.sleep(period_in_ms)
            print("EMG data:", emg)
            frames_to_stream -= 1

        print("Finished")

    except (KeyboardInterrupt, SystemExit):
        print('\n! Received keyboard interrupt, quitting emg streaming\n')

    if is_streaming:
        emg.stop_streaming()
        print("Emg streaming was stopped")


if __name__ == '__main__':
    main()
