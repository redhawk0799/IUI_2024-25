#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import _setup_sys_path

from teslasuit_sdk import ts_api
import teslasuit_sdk.subsystems.ts_current_feedback

def main():
    is_streaming = False
    try:
        print("Initialize API")
        api = ts_api.TsApi()
        
        device = api.get_device_manager().get_or_wait_last_device_attached()
        current_feedback = device.current_feedback

        print("Wait for current_feedback data...")
        current_feedback.start_streaming()
        is_streaming = True

        nodes_data = {}
        
        while True:
            data = current_feedback.get_data_on_ready()
            print(data.nodes[0].number_of_channels)
            
            for i in range(0, data.nodes[0].number_of_channels):
                if nodes_data.get(data.nodes[0].node_index) == None:
                    nodes_data[data.nodes[0].node_index] = {}
                    
                nodes_data[data.nodes[0].node_index][data.nodes[0].channels_data[i].channel_index] = data.nodes[0].channels_data[i].value
                print("node index: {} || channel index: {} || chanel value: {}".format(data.nodes[0].node_index, data.nodes[0].channels_data[i].channel_index, data.nodes[0].channels_data[i].value))
             
            if (len(nodes_data.keys()) == 5):    # use 3 if jacket and 5 if jacket + pants
                break
    
    print(nodes_data)

    except (KeyboardInterrupt, SystemExit):
        print('\n! Received keyboard interrupt, quitting streaming\n')

    if is_streaming:
        current_feedback.stop_streaming()
        print("current feedback streaming was stopped")


if __name__ == '__main__':
    main()
