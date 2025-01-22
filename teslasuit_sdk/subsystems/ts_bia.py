from ctypes import (c_uint8, POINTER,
                    pointer, Structure,
                    c_uint64, c_int, c_uint32,
                    CFUNCTYPE, c_void_p, cast)
from teslasuit_sdk.ts_types import TsDeviceHandle
import time

class TsBiaConfig(Structure):
    _pack_ = 1
    _fields_ = [("channels", POINTER(c_uint32)),
                ("number_of_channels", c_uint32),
                ("start_frequency", c_uint32),
                ("frequency_step", c_uint32),
                ("number_of_steps", c_uint32)]

class TsComplexNumber(Structure):
    _pack_ = 1
    _fields_ = [('real_value', c_int),
                ('im_value', c_int)]


class TsBiaFrequencyData(Structure):
    _pack_ = 1
    _fields_ = [('frequency', c_uint32),
                ('complex_number', TsComplexNumber)]


class TsBiaChannelData(Structure):
    _pack_ = 1
    _fields_ = [('channel_index', c_uint32),
                ('number_of_frequencies', c_uint64),
                ('frequencies', POINTER(TsBiaFrequencyData))]


class TsBiaChannels(Structure):
    _pack_ = 1
    _fields_ = [('number_of_channels', c_uint32),
                ('channels', POINTER(TsBiaChannelData))]

class TsBia:
    def __init__(self, lib, device):
        self.__lib = lib
        self.__device = device

        self.__is_started = False
        self.__is_data_ready = False

        self.__data = TsBiaChannels()

    def start_streaming(self):
        if self.__is_started:
            return

        self.__subscribe_on_data_update()

        self.__lib.ts_bia_start_streaming(self.__device)
        self.__is_started = True

    def stop_streaming(self):
        if not self.__is_started:
            return

        self.__lib.ts_bia_stop_streaming(self.__device)
        self.__is_started = False

    def get_data_on_ready(self):
        while not self.__is_data_ready and self.__is_started:
            time.sleep(0.001)

        self.__is_data_ready = False
        return self.__data

    def set_streaming_config(self, channels, start_frequency=10000, number_of_steps=10, frequency_step=10000):
        converted_channels = (c_uint32 * len(channels))(*channels)
        
        config = TsBiaConfig()
        
        config.channels = cast(converted_channels, POINTER(c_uint32))
        config.number_of_channels = len(channels)
        config.start_frequency = c_uint32(start_frequency)
        config.number_of_steps = c_uint32(number_of_steps)
        config.frequency_step = c_uint32(frequency_step)
        
        self.__lib.ts_bia_set_streaming_config(self.__device,  pointer(config))
    
    def __subscribe_on_data_update(self):
        def __on_updated_callback(device, data_ptr, user_data):
            self.__data.number_of_channels = self.__get_number_of_channels(data_ptr)
            self.__data.channels = (TsBiaChannelData * self.__data.number_of_channels)()
   
            channels_indexes = self.__get_channels_indexes(data_ptr, self.__data.number_of_channels)               
            
            for i, channel_index in enumerate([*channels_indexes]):
                self.__data.channels[i].channel_index = channel_index
                 
                number_of_frequencies = self.__get_channel_frequencies_size(data_ptr, channel_index)
                channel_frequencies = self.__get_channel_frequencies(data_ptr, channel_index, number_of_frequencies)
                
                frequencies_data = (TsBiaFrequencyData * number_of_frequencies)()
                self.__data.channels[i].number_of_frequencies = number_of_frequencies
                self.__data.channels[i].frequencies = cast(frequencies_data, POINTER(TsBiaFrequencyData))
                
                for j, frequency in enumerate([*channel_frequencies]):
                    frequency_value = self.__get_channel_frequency_complex_value(data_ptr, channel_index, frequency)
                    frequencies_data[j].frequency = frequency
                    frequencies_data[j].complex_number = frequency_value
            
            self.__is_data_ready = True

        data_callback_prototype = CFUNCTYPE(None, POINTER(TsDeviceHandle), c_void_p, c_void_p)
        self.__data_callback = data_callback_prototype(__on_updated_callback)
        self.__lib.ts_bia_set_update_callback(self.__device, self.__data_callback,
                                              c_void_p())

    def __get_channels_indexes(self, data_ptr , number_of_channels):
        indexes = (c_uint32 * number_of_channels)()
        self.__lib.ts_bia_get_channels_indexes(c_void_p(data_ptr), pointer(indexes), c_uint64(number_of_channels))
        
        return indexes
        
    def __get_number_of_channels(self, data_ptr):
        number_of_channels = c_uint64(0)
        self.__lib.ts_bia_get_number_of_channels(c_void_p(data_ptr), pointer(number_of_channels))

        return number_of_channels.value

    def __get_channel_frequencies_size(self, data_ptr, channel_index):
        number_of_frequencies = c_uint64(0)
        self.__lib.ts_bia_get_channel_number_of_frequencies(c_void_p(data_ptr), 
                                                            c_uint32(channel_index), 
                                                            pointer(number_of_frequencies))
        
        return number_of_frequencies.value

    def __get_channel_frequencies(self, data_ptr, channel_index, number_of_frequencies):
        frequencies = (c_uint32 * number_of_frequencies)()
        self.__lib.ts_bia_get_channel_frequencies(c_void_p(data_ptr), c_uint32(channel_index),
                                                  pointer(frequencies), c_uint64(number_of_frequencies))
                                                  
        return frequencies

    def __get_channel_frequency_complex_value(self,
                                              data_ptr,
                                              channel_index,
                                              frequency):
        complex_number = TsComplexNumber()
        self.__lib.ts_bia_get_channel_frequency_complex_value(c_void_p(data_ptr),
                                                              c_uint32(channel_index),
                                                              c_uint32(frequency),
                                                              pointer(complex_number))
        return complex_number
