import time

from ctypes import (pointer, c_int, 
                    cast, POINTER, c_void_p, CFUNCTYPE)

from teslasuit_sdk import ts_types
from teslasuit_sdk.ts_device import TsDevice

class TsDeviceManager:
    def __init__(self, lib):
        self.__lib = lib
        self.devices = []
        self.__devices_event_callback = None
        self.__subscribe_on_device_events()
    
    def __subscribe_on_device_events(self):
        def __on_device_event(device_ptr, device_event, user_data):
            if device_event == ts_types.TsDeviceEvent.TsDeviceEvent_DeviceAttached:
                self.__add_device(device_ptr.contents)
            elif device_event == ts_types.TsDeviceEvent.TsDeviceEvent_DeviceDetached:
                self.__remove_device(device_ptr.contents)
        
        devices_event_callback = CFUNCTYPE(None, POINTER(ts_types.TsDevice), c_int, c_void_p)   
        self.__devices_event_callback = devices_event_callback(__on_device_event)
 
        self.__lib.ts_set_device_event_callback(ts_types.TsDeviceEventPolicy.TsDeviceEventPolicy_Enumerate, self.__devices_event_callback, c_void_p())
        
    def __add_device(self, ts_device):
        self.devices.append(TsDevice(self.__lib, ts_device))
        print("Device connected:", str(ts_device))

    def __remove_device(self, ts_device): 
        print("Device disconnected:", str(ts_device))
        self.devices = [d for d in self.devices if str(d.device_uuid.uuid) != str(ts_device.uuid)]

    def wait_for_device_to_connect(self, number_of_devices_to_wait=1):
        while len(self.devices) < number_of_devices_to_wait:
            print('Waiting for a device connect...')
            time.sleep(3)

    def get_or_wait_last_device_attached(self):
        if len(self.devices) == 0:
            self.wait_for_device_to_connect()
        return self.devices[len(self.devices) - 1]
        