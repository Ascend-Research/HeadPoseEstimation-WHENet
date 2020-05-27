# !/usr/bin/env python
# -*- coding:utf-8 -*-

import threading
import socket
import time
import struct
import time
from .presenter_types import *



class AgentSocket(object):
    def __init__(self, server_ip, port):
        self._server_address = (server_ip, port)
        self._sock_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def Connect(self):
        ret = 0
        for i in range(0,5):
            ret = self._sock_client.connect_ex(self._server_address)
            if ret == 0:
                break

        return ret


    def _ReadSocket(self, read_len):
        has_read_len = 0
        read_buf = b''
        total_buf = b''

        while has_read_len != read_len:
            
            try:
                read_buf = self._sock_client.recv(read_len - has_read_len)
            except socket.error:
                print("socket error")
                return False, None
            if read_buf == b'':

                return False, None
            total_buf += read_buf
            has_read_len = len(total_buf)
        
        return True, total_buf

    def _ReadMsgHead(self, read_len):
        ret, msg_head = self._ReadSocket(read_len)
        #print("msg head data is :", msg_head)
        if not ret:
            print("socket receive msg head null")
            return None, None

        # in Struct(), 'I' is unsigned int, 'B' is unsigned char
        msg_head_data = struct.Struct('IB')
        (msg_total_len, msg_name_len) = msg_head_data.unpack(msg_head)
        msg_total_len = socket.ntohl(msg_total_len)
        #print("msg total length is :", msg_total_len)
        #print("msg name is :", msg_name_len)
        return msg_total_len, msg_name_len

    def _ReadMsgName(self, msg_name_len):
        ret, msg_name = self._ReadSocket(msg_name_len)
        #print("direct msg name is :", msg_name)
        if not ret:
            print("socket receive msg name null")
            return False, None
        try:
            msg_name = msg_name.decode("utf-8")
            #print("decode msg name is :", msg_name)
        except Exception as e:
            print("msg name decode to utf-8 error")
            return False, None

        return True, msg_name

    def _ReadMsgBody(self, msg_body_len):
        #print("msg body length is :", msg_body_len)
        ret, msg_body = self._ReadSocket(msg_body_len)
        if not ret:
            print("socket receive msg body null")
            return False, None
        return True, msg_body

    def RecvMsg(self):
        # Step1: read msg head
        msg_total_len, msg_name_len = self._ReadMsgHead(5)
        if msg_total_len is None:
            print("msg_total_len is None.")
            return None

        # Step2: read msg name
        ret, msg_name = self._ReadMsgName(msg_name_len)
        if not ret:
            return None

        # Step3:  read msg body
        msg_body_len = msg_total_len - 5 - msg_name_len
        if msg_body_len < 0:
            print("msg_total_len is 0")
            return None
        ret, msg_body = self._ReadMsgBody(msg_body_len)
        if not ret:
            return None

        return msg_name, msg_body


    def SendMsg(self, data):
        try:
            self._sock_client.sendall(data)
        except Exception as e:
            print("send msg failed")
            return 1
        return 0


    def Close(self):
        self._bstart = False
        self._sock_client.shutdown(socket.SHUT_RDWR)
        self._sock_client.close()
