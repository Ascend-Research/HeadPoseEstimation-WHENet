# !/usr/bin/env python
# -*- coding:utf-8 -*-

import multiprocessing
from multiprocessing import Process, Array, Value, Queue
from threading import Thread
from ctypes import c_char_p
import os
import time
from . import presenter_message as pm
from .presenter_types import *
from .presenter_agent import *
import socket
import struct
import configparser


class PresenterChannel():
    def __init__(self, server_ip, port, channel_name='video', channel_type = CONTENT_TYPE_VIDEO):
        self.server_ip = server_ip
        self.port = port
        self.channel_name = channel_name
        self.channel_type = channel_type
        self.msg_queue = Queue()
        self.open_status = None

    def Startup(self):
        self.open_status = multiprocessing.Manager().Value('i', STATUS_DISCONNECT)  # connect status
        agent_process = Process(target=StartPresenterAgent, args=(self.msg_queue, self.server_ip, self.port, self.open_status))
        agent_process.start()
        time.sleep(0.5)

        self.SendOpenChannelRequest(self.channel_name, self.channel_type)

        return self.WaitOpenStatus(STATUS_OPENED)

    def WaitOpenStatus(self, listen_status):
        ret = STATUS_ERROR
        for i in range(0, 100):
            time.sleep(0.1)
            if self.open_status.value == listen_status:
                print("Open status is %d now"%(listen_status))
                ret = STATUS_OK
                break

        return ret

    def SendMessage(self, data):
        self.msg_queue.put(data)

    def SendOpenChannelRequest(self, channel_name, content_type):
        request_msg = pm.OpenChannelRequest(channel_name, content_type)
        self.SendMessage(request_msg)

    def SendDetectionData(self, image_width, image_height, image_data, detection_result):
        request_msg = pm.ImageFrameRequest(image_width, image_height, image_data, detection_result)
        self.SendMessage(request_msg)
    # ruochen: rect
    def SendRect(self, left,right,top,bottom, text):
        request_msg = pm.RectangleAttr(left,right,top,bottom, text)
        self.SendMessage(request_msg)
    # ruochen: point
    def SendDetectionPoint(self, point_item):
        request_msg = pm.Coordinate(point_item)
        self.SendMessage(request_msg)

    def SendHeartBeatMessage(self):
        msg = pm.HeartBeatMessage()
        self.SendMessage(msg)

    def __del__(self):
        self.open_status.value = STATUS_EXITING
        print("Presenter channel close...")
        self.SendHeartBeatMessage()
        if STATUS_OK == self.WaitOpenStatus(STATUS_EXITTED):
            print("Presenter channel closed")
        else:
            print("Presenter channel close failed for presenter agent no response")

def GetPresenterServerAddr(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    print(config.sections())
    presenter_server_ip = config['baseconf']['presenter_server_ip']
    port = int(config['baseconf']['presenter_server_port'])
	
    print("presenter server ip %s, port %d"%(presenter_server_ip, port))
    return presenter_server_ip, port

def OpenChannel(config_file, channel_name='video', channel_type = CONTENT_TYPE_VIDEO):
    server_ip, port = GetPresenterServerAddr(config_file)
    channel = PresenterChannel(server_ip, port, channel_name, channel_type)
    ret = channel.Startup()
    if ret:
        print("Open channel failed")
        return None
    return channel
