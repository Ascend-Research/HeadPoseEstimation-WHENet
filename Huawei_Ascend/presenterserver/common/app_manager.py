#   =======================================================================
#
# Copyright (C) 2018, Hisilicon Technologies Co., Ltd. All Rights Reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   1 Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#
#   2 Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
#   3 Neither the names of the copyright holders nor the names of the
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#   =======================================================================
#
"""presenter app manager module"""

import time
import threading
import logging
from common.channel_manager import ChannelManager

# Heartbeat timeout, exceeding the limit, the socket will disconnect
HEARTBEAT_TIMEOUT = 100

class App():
    '''App class, When receive an app request from
       Presenter Agent, creat an object.
    '''
    def __init__(self, app_id, conn=None):
        self.app_id = app_id
        self.heartbeat = time.time()
        self.socket_fd = conn.fileno()
        # set timeout 1 second
        conn.settimeout(1)
        self.socket = conn
        self.frame_num_dict = {}

class AppManager():
    '''A class provides app management features'''
    __instance = None
    channel_manager = None
    app_list_lock = threading.Lock()
    app_list = []
    thread_switch = False

    def __init__(self):
        """init func"""


    def __new__(cls):
        """ensure only a single instance created. """
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            cls.channel_manager = ChannelManager([])
            cls._create_thread()
        return cls.__instance

    @classmethod
    def _create_thread(cls):
        """_create_thread."""

        thread = threading.Thread(target=cls._app_thread)
        thread.start()

    @classmethod
    def _app_thread(cls):
        """background thread to process video"""
        logging.info('create app manager thread')
        while True:
            if cls.thread_switch:
                break
            for i in range(len(cls.app_list)):
                if time.time() - cls.app_list[i].heartbeat > HEARTBEAT_TIMEOUT:
                    app_id = cls.app_list[i].app_id
                    cls.channel_manager.unregister_one_channel(app_id)
                    del cls.app_list[i]
                    logging.info("unregister app: %s", app_id)
            time.sleep(1)

    def set_thread_switch(self):
        AppManager.thread_switch = True

    def register_app(self, app_id, socket):
        """
        API for registering an app
        Args:
            app_id: app id, must be globally unique
            socket: a socket communicating with the app
        """
        with self.app_list_lock:
            for i in range(len(self.app_list)):
                if self.app_list[i].app_id == app_id:
                    return False

            app = App(app_id, socket)
            self.app_list.append(app)
            self.channel_manager.register_one_channel(app_id)
            logging.info("register app: %s", app_id)
            return True

    def unregister_app_by_fd(self, sock_fileno):
        """
        API for unregistering an app
        Args:
            sock_fileno: sock_fileno is binded to an app.
                         Through it, find the app and delete it.
        """
        with self.app_list_lock:
            for i in range(len(self.app_list)):
                if self.app_list[i].socket_fd == sock_fileno:
                    app_id = self.app_list[i].app_id
                    self.channel_manager.unregister_one_channel(app_id)
                    del self.app_list[i]
                    logging.info("unregister app: %s", app_id)
                    break

    def get_socket_by_app_id(self, app_id):
        """
        API for finding an app
        Args:
            app_id: the id of an app.
        """
        with self.app_list_lock:
            for i in range(len(self.app_list)):
                if self.app_list[i].app_id == app_id:
                    return self.app_list[i].socket
            return None

    def get_app_id_by_socket(self, sock_fd):
        """
        API for get app id by socket
        Args:
            sock_fd: sock_fd is binded to an app.
                         Through it, find the app and delete it.
        """
        with self.app_list_lock:
            for i in range(len(self.app_list)):
                if self.app_list[i].socket_fd == sock_fd:
                    return self.app_list[i].app_id
            return None

    def is_app_exist(self, app_id):
        """
        API for checking if the app exist
        Args:
            app_id: the id of an app.
        """
        with self.app_list_lock:
            for i in range(len(self.app_list)):
                if self.app_list[i].app_id == app_id:
                    return True
            return False

    def get_app_num(self):
        """
        API for getting the number of apps
        Args: NA
        """
        with self.app_list_lock:
            return len(self.app_list)

    def set_heartbeat(self, sock_fileno):
        with self.app_list_lock:
            for i in range(len(self.app_list)):
                if self.app_list[i].socket_fd == sock_fileno:
                    self.app_list[i].heartbeat = time.time()

    def increase_frame_num(self, app_id, channel_id):
        with self.app_list_lock:
            for i in range(len(self.app_list)):
                if self.app_list[i].app_id == app_id:
                    if channel_id in self.app_list[i].frame_num_dict:
                        self.app_list[i].frame_num_dict[channel_id] += 1
                    else:
                        self.app_list[i].frame_num_dict[channel_id] = 1

    def get_frame_num(self, app_id, channel_id):
        with self.app_list_lock:
            for i in range(len(self.app_list)):
                if self.app_list[i].app_id == app_id:
                    if channel_id in self.app_list[i].frame_num_dict:
                        return self.app_list[i].frame_num_dict[channel_id]
                    else:
                        return 0
            return 0
    def list_app(self):
        """
        API for listing all apps
        Args: NA
        """
        with self.app_list_lock:
            return [self.app_list[i].app_id for i in range(len(self.app_list))]
