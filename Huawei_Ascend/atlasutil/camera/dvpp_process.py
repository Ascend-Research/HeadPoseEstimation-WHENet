# !/usr/bin/env python
# -*- coding:utf-8 -*-  

import ctypes
from ctypes import *
import os
import numpy as np
import time

JPGENC_FORMAT_NV12 = 0x10

class CameraImageBuf(Structure):
    _fields_ = [
        ('size', c_uint),
        ('data', POINTER(c_ubyte))
    ]

class DvppImageBuffer(Structure):
     _fields_ = [
        ('format', c_uint),
        ('buf_size', c_uint),
        ('width', c_uint),
        ('height', c_uint),
        ('image_size', c_uint),
        ('data', POINTER(c_ubyte)),
    ]

class DvppProcess():
    lib = ctypes.CDLL(os.path.dirname(os.path.abspath(__file__)) + '/libdvppprocess.so')

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.size = int(width * height * 3 / 2)
        self.yuv_buf = (c_ubyte * self.size)()
        self.jpeg_buf = CameraImageBuf()
        self.jpeg_buf.size = width * height * 3
        self.jpeg_buf.data = (c_ubyte * self.jpeg_buf.size)()
        DvppProcess.lib.InitDvpp(self.width, self.height)

    def Yuv2Jpeg(self, in_yuv_data):
        if not in_yuv_data.flags['C_CONTIGUOUS']:
            in_yuv_data = np.ascontiguousarray(in_yuv_data.ctypes.data, POINTER(c_ubyte))
        DvppProcess.lib.CvtYuv2Jpeg(byref(self.jpeg_buf), in_yuv_data.ctypes.data_as(c_char_p))
        array = (ctypes.c_ubyte * self.jpeg_buf.size).from_address(ctypes.addressof(self.jpeg_buf.data.contents))
        image_array = np.ndarray(buffer=array, dtype=np.uint8, shape=(self.jpeg_buf.size))
        return image_array
