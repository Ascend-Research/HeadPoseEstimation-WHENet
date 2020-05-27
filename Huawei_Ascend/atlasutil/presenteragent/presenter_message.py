# !/usr/bin/env python
# -*- coding:utf-8 -*-


from ctypes import c_char_p
import os
import time
from . import presenter_message_pb2 as pb2
from .presenter_types import *
import struct
import socket


def PackMessage(msg_name, msg_data):
    buf = msg_data.SerializeToString()
    msg_body_len = len(buf)
    #print('msg_name:', msg_name)
    msg_name_len = len(msg_name)
    msg_total_len = msg_name_len + msg_body_len + 5
    #print('msg_total_len:', msg_total_len)
    data = b''
    msg_total_len = socket.htonl(msg_total_len)
    # print('socket.htonl(msg_total_len)=', msg_total_len)
    pack_data = struct.pack('IB', msg_total_len, msg_name_len)
    #print('pack_data length=', len(pack_data))
    data += pack_data
    data += msg_name.encode()
    data += buf
    return data


def OpenChannelRequest(channel_name, content_type):
    request = pb2.OpenChannelRequest()
    request.channel_name = channel_name
    request.content_type = content_type

    return PackMessage(pb2._OPENCHANNELREQUEST.full_name, request)


def ImageFrameRequest(image_width, image_height, image_data, detection_result):
    request = pb2.PresentImageRequest()
    request.format = 0
    request.width = image_width
    request.height = image_height
    request.data = image_data
    for i in range(0, len(detection_result)):
        myadd = request.rectangle_list.add()
        myadd.left_top.x = detection_result[i].lt.x
        myadd.left_top.y = detection_result[i].lt.y
        myadd.right_bottom.x = detection_result[i].rb.x
        myadd.right_bottom.y = detection_result[i].rb.y
        myadd.label_text = detection_result[i].result_text

    return PackMessage(pb2._PRESENTIMAGEREQUEST.full_name, request)

def RectangleAttr(left,right,top,bottom, text):
    request = pb2.Rectangle_Attr()
    request.left_top.x = left
    request.left_top.y = right
    request.right_bottom.x = top
    request.right_bottom.y = bottom
    request.label_text = text
    return PackMessage(pb2._RECTANGLE_ATTR.full_name, request)

def Coordinate(point_item):
    request = pb2.Coordinate()
    request.x = point_item.x
    request.y = point_item.y
    return PackMessage(pb2._COORDINATE.full_name, request)

def HeartBeatMessage():
    return PackMessage(pb2._HEARTBEATMESSAGE.full_name, pb2.HeartbeatMessage())


def IsOpenChannelResponse(msg_name):
    return (msg_name == pb2._OPENCHANNELRESPONSE.full_name)




