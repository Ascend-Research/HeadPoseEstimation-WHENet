# !/usr/bin/env python
# -*- coding:utf-8 -*-

from .socket_client import *
from .presenter_types import *
from . import presenter_message as pm
from threading import Thread

class PresenterAgent():
    def __init__(self, server_ip, port):
        self.socket = AgentSocket(server_ip, port)
        self.exit = False

    def ConnectServer(self):
        return self.socket.Connect()

    def StartHeardBeatThread(self):
        self.heart_beat_thread = Thread(target=self.KeepAlive)
        self.heart_beat_thread.start()

    def KeepAlive(self):
        msg = pm.HeartBeatMessage()

        while True:
            if self.exit:
                print("Heard beat thread exit")
                break
            self.socket.SendMsg(msg)
            time.sleep(2)

    def Exit(self):
        self.socket.Close()
        self.exit = True

def StartPresenterAgent(msg_queue, server_ip, port, open_status):
    agent = PresenterAgent(server_ip, port)
    ret = agent.ConnectServer()
    if ret:
        print("Connect server failed")
        return

    open_status.value = STATUS_CONNECTED
    print("Connect to presenter server ok")

    while True:
        data = msg_queue.get()

        if open_status.value == STATUS_EXITING:
            open_status.value = STATUS_EXITTED
            agent.Exit()
            break

        if data:
            agent.socket.SendMsg(data)

        msg_name, msg_body = agent.socket.RecvMsg()
        if (msg_name == None) or (msg_body == None):
            print("Recv invalid message, message name ", msg_name)
            continue

        if (open_status.value == STATUS_CONNECTED) and pm.IsOpenChannelResponse(msg_name):
            print("Received open channel respone")
            open_status.value = STATUS_OPENED
            agent.StartHeardBeatThread()
            print("presenter agent change connect_status to ", open_status.value)

