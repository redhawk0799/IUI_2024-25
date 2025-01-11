#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import _setup_sys_path

from teslasuit_sdk import ts_api
import teslasuit_sdk.subsystems.ts_ppg 

def main():
    is_streaming = False
    try:
        print("Initialize API")
        api = ts_api.TsApi()
        
        device = api.get_device_manager().get_or_wait_last_device_attached()
        ppg = device.ppg

        print("Wait for ppg data...")
        ppg.start_raw_streaming()
        is_streaming = True

        while True:
            data = ppg.get_data()

            if data.number_of_nodes > 0:
                print(f'Heart rate: {data.nodes[0].heart_rate}')

            time.sleep(1)

        print("Finished")

    except (KeyboardInterrupt, SystemExit):
        print('\n! Received keyboard interrupt, quitting ppg streaming\n')

    if is_streaming:
        ppg.stop_raw_streaming()
        print("Ppg streaming was stopped")


if __name__ == '__main__':

    main()
