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
        bia = device.bia

        print("Setup channels and frequencies")
        channels_indexes = [1, 3, 7, 9, 12]
        bia.set_streaming_config(channels_indexes, 24000, 1, 1000)

        print("Streaming...")
        bia.start_streaming()
        
        while True:
            data = bia.get_data_on_ready()
            print(data.number_of_channels)
            
            for i in range(0, data.number_of_channels):
                print("channel index: ", data.channels[i].channel_index)
                for j in range(0, data.channels[i].number_of_frequencies):
                    print("real = ", data.channels[i].frequencies[j].complex_number.real_value)
                    print("im = ", data.channels[i].frequencies[j].complex_number.im_value)
        
        is_streaming = True

        print("Finished")

    except (KeyboardInterrupt, SystemExit):
        print('\n! Received keyboard interrupt, quitting bia streaming\n')

    if is_streaming:
        bia.stop_streaming()
        print("Bia streaming was stopped")


if __name__ == '__main__':
    main()
