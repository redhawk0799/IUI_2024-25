from ctypes import (c_uint8, POINTER,
                    pointer, Structure,
                    c_uint64, c_uint32,
                    CFUNCTYPE, c_void_p, cast)
from teslasuit_sdk.ts_types import TsDeviceHandle
import time

class TsCurrentFeedbackChannelData(Structure):
    _pack_ = 1
    _fields_ = [('channel_index', c_uint32),
                ('value', c_uint32)]

class TsCurrentFeedbackNodeData(Structure):
    _pack_ = 1
    _fields_ = [('node_index', c_uint32),
                ('number_of_channels', c_uint32),
                ('channels_data', POINTER(TsCurrentFeedbackChannelData))]

class TsCurrentFeedbackNodes(Structure):
    _pack_ = 1
    _fields_ = [('number_of_nodes', c_uint32),
                ('nodes', POINTER(TsCurrentFeedbackNodeData))]

class TsCurrentFeedback:
    def __init__(self, lib, device):
        self.__lib = lib
        self.__device = device

        self.__is_started = False
        self.__is_data_ready = False

        self.__data = TsCurrentFeedbackNodes()

    def start_streaming(self):
        if self.__is_started:
            return

        self.__subscribe_on_data_update()

        self.__lib.ts_current_feedback_start_streaming(self.__device)
        self.__is_started = True

    def stop_streaming(self):
        if not self.__is_started:
            return

        self.__lib.ts_current_feedback_stop_streaming(self.__device)
        self.__is_started = False

    def get_data_on_ready(self):
        while not self.__is_data_ready and self.__is_started:
            time.sleep(0.001)

        self.__is_data_ready = False
        return self.__data

    def __subscribe_on_data_update(self):
        def __on_updated_callback(device, data_ptr, user_data):
            self.__data.number_of_nodes = self.__get_number_of_nodes(data_ptr)
            self.__data.nodes = (TsCurrentFeedbackNodeData * self.__data.number_of_nodes)()

            nodes_indexes = self.__get_nodes_indexes(data_ptr, self.__data.number_of_nodes)

            for i, node_index in enumerate([*nodes_indexes]):              
                number_of_channels = self.__get_number_of_node_channels(data_ptr, node_index)
                
                self.__data.nodes[i].node_index = node_index
                self.__data.nodes[i].number_of_channels = number_of_channels
                
                channels_data = (TsCurrentFeedbackChannelData * number_of_channels)()
                self.__data.nodes[i].channels_data = cast(channels_data, POINTER(TsCurrentFeedbackChannelData))
                                     
                channels_indexes = self.__get_channels_indexes(data_ptr, node_index, number_of_channels)
                 
                for j, channel_index in enumerate([*channels_indexes]):          
                    channels_data[j].channel_index = channel_index
                    channels_data[j].value = self.__get_channel_value(data_ptr, node_index, channel_index)
            
            self.__is_data_ready = True

        data_callback_prototype = CFUNCTYPE(None, POINTER(TsDeviceHandle), c_void_p, c_void_p)
        self.__data_callback = data_callback_prototype(__on_updated_callback)
        self.__lib.ts_current_feedback_set_update_callback(self.__device, self.__data_callback,
                                              c_void_p())

    def __get_number_of_nodes(self, data_ptr):
        number_of_nodes = c_uint64(0)
        self.__lib.ts_current_feedback_get_number_of_nodes(c_void_p(data_ptr), pointer(number_of_nodes))
        
        return number_of_nodes.value
        
    def __get_nodes_indexes(self, data_ptr, number_of_nodes):
        indexes = (c_uint8 * number_of_nodes)()
        self.__lib.ts_current_feedback_get_nodes_indexes(c_void_p(data_ptr), pointer(indexes), c_uint64(number_of_nodes))
        
        return indexes

    def __get_number_of_node_channels(self, data_ptr, node_index):
        number_of_channels = c_uint64(0)
        self.__lib.ts_current_feedback_get_number_of_node_channels(c_void_p(data_ptr), c_uint8(node_index), pointer(number_of_channels))
        
        return number_of_channels.value

    def __get_channels_indexes(self, data_ptr, node_index, number_of_channels):
        indexes = (c_uint32 * number_of_channels)()
        self.__lib.ts_current_feedback_get_channels_indexes(c_void_p(data_ptr), c_uint8(node_index), pointer(indexes), c_uint64(number_of_channels))
        
        return indexes

    def __get_channel_value(self, data_ptr, node_index, channel_index):
        channel_value = c_uint32(0)
        self.__lib.ts_current_feedback_get_channel_value(c_void_p(data_ptr),
                                                              c_uint8(node_index),
                                                              c_uint32(channel_index),
                                                              pointer(channel_value))
        return channel_value.value
