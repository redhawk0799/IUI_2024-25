#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from teslasuit_sdk import ts_loader
from teslasuit_sdk import ts_device_manager
from teslasuit_sdk.ts_mapper import TsMapper
from teslasuit_sdk.ts_asset_manager import TsAssetManager

from ctypes import c_char_p

class TsApi:
    """
    An aggregate TESLASUIT API class that contains C API library loader and device manager.

    Attributes
    ----------
    lib : CDLL
        a loaded TESLASUIT C API library object
    version : TsVersion
        the version of loaded and used C API
    device_manager : TsDeviceManager
        a class that provides access to TESLASUIT devices
    """
    def __init__(self, lib_path=None):
        self.__lib = None
        self.__initialized = False

        self.__load_library(lib_path)

        code = self.__lib.ts_initialize()
        if code != 0:
            get_status_message = self.__lib.ts_get_status_code_message
            get_status_message.restype = c_char_p
            
            message = get_status_message(code)
            raise Exception(message.decode('utf-8'))
        
        self.mapper = TsMapper(self.__lib)
        self.asset_manager = TsAssetManager(self.__lib)
        self.__device_manager = ts_device_manager.TsDeviceManager(self.__lib)

    def __load_library(self, lib_path=None):
        loader = ts_loader.TsLoader(lib_path)
        self.__lib = loader.load()

    def __unload_library(self):
        del self.__lib
        
    def get_device_manager(self):
        return self.__device_manager

    def __del__(self):
        self.__lib.ts_uninitialize()
        print('TS API uninitialized')
        
        self.__unload_library()
