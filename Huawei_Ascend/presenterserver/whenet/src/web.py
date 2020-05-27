# -*- coding: UTF-8 -*-
#
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
"""
web application for presenter server.
"""
import os
import re
import random
import base64
import threading
import time
import logging
import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.websocket
import whenet.src.config_parser as config_parser
from common.channel_manager import ChannelManager

class WebApp:
    """
    web application
    """
    __instance = None
    def __init__(self):
        """
        init method
        """
        self.channel_mgr = ChannelManager(["image", "video"])

        self.request_list = set()

        self.lock = threading.Lock()

    def __new__(cls, *args, **kwargs):

        # if instance is None than create one
        if cls.__instance is None:
            cls.__instance = object.__new__(cls, *args, **kwargs)
        return cls.__instance

    def add_channel(self, channel_name):
        """
        add channel

        @param channel_name  name of channel
        @return: return add status and message (for error status)

        """
        ret = {"ret":"error", "msg":""}

        # check channel_name validate,
        # channel_name can not be None or length = 0
        if channel_name is None:
            logging.info("Channel name is None , add channel failed")
            ret["msg"] = "Channel name can not be empty"
            return ret

        # strip channel name
        channel_name = channel_name.strip()

        # check channel_name emtpy or not
        if channel_name == "":
            logging.info("Channel name is emtpy , add channel failed")
            ret["msg"] = "Channel name can not be empty"
            return ret


        # length of channel name can not over 25
        if len(channel_name) > 25:
            logging.info("Length of channel name %s > 25 , add channel failed", channel_name)
            ret["msg"] = "Length of channel name should less than 25"
            return ret

        # define pattern support a-z A-Z and /
        pattern = re.compile(r"[a-z]|[A-Z]|[0-9]|/")
        tmp = pattern.findall(channel_name)

        # check reuslt changed or not
        if len(tmp) != len(channel_name):
            logging.info("%s contain invalidate character, add channel failed", channel_name)
            ret["msg"] = "Channel name only support 0-9, a-z, A-Z /"
            return ret

        # register channel
        flag = self.channel_mgr.register_one_channel(channel_name)

        #  check register result
        if self.channel_mgr.err_code_too_many_channel == flag:
            logging.info("Only supports up to 10 channels, add channel failed")
            ret["msg"] = "Only supports up to 10 channels"

        elif self.channel_mgr.err_code_repeat_channel == flag:
            logging.info("%s already exist, add channel failed", channel_name)
            ret["msg"] = "Channel %s already exist" % channel_name

        else:
            logging.info("add channel %s succeed", channel_name)
            ret["ret"] = "success"

        return ret

    def del_channel(self, names):
        """
        delete channel

        @param names: channel name to be deleted, separated by ','
        @return: return add status and message (for error status)
        """

        # init ret for return
        ret = {"ret":"error", "msg":""}

        # check length of names
        if names.strip() == "":
            logging.info("Channel name is empty, delete channel failed")
            ret["msg"] = "Channel name should not be empty"
            return ret

        # split name for multi name
        listname = names.split(",")

        # unregister name
        for item in listname:
            item = item.strip()

            # if name is emtpy continu
            if item == "":
                continue

            self.channel_mgr.unregister_one_channel(item)
            logging.info("delete channel %s succeed", item)

        ret["ret"] = "success"

        return ret


    def list_channels(self):
        """
        list all channels information
        """

        # list register channels
        ret = self.channel_mgr.list_channels()

        # id for every channel item , start with 1
        idx = 1

        # set id for channel
        for item in ret:
            item['id'] = idx
            idx = idx + 1

        return ret

    def is_channel_exists(self, name):
        """
        view channel content via browser.

        @param  name : channel name
        @return return True if exists. otherwise return False.
        """
        return  self.channel_mgr.is_channel_exist(name)


    def add_requst(self, request):
        """
        add request

        @param  requst: request item to be stored

        @note: request can not be same with other request.
               request is identified by   (channel name ,random number)
               so this method do not return value.
        """
        with self.lock:
            self.request_list.add(request)

    def has_request(self, request):
        """
        whether request exist or not

        @param  request:  request to be checked.
        @return:  return True if exists, otherwise return False.
        """
        with self.lock:

            for item in self.request_list:

                # check request equal
                if item[0] == request[0] and item[1] == request[1]:
                    return True

            return False

    def get_media_data(self, channel_name):
        """
        get media data by channel name

        @param channel_name: channel to be quest data.
        @return return dictionary which have for item
                 type: identify channel type, for image or video.
                 image: data to be returned.
                 fps:   just for video type
                 status:  can be error, ok, or loading.
        """
        # channel exists or not
        if self.is_channel_exists(channel_name) is False:
            return {'type': 'unkown', 'image':'', 'fps':0, 'status':'error'}

        image_data = self.channel_mgr.get_channel_image(channel_name)
        # only for image type.
        if image_data is not None:
            image_data = base64.b64encode(image_data).decode('utf-8')
            return {'type': 'image', 'image':image_data, 'fps':0, 'status':'ok'}


        fps = 0    # fps for video
        image = None    # image for video & image
        rectangle_list = None
        handler = self.channel_mgr.get_channel_handler_by_name(channel_name)

        if handler is not None:
            media_type = handler.get_media_type()

            # if type is image then get image data
            if media_type == "image":
                image = handler.get_image_data()

            # for video
            else:
                frame_info = handler.get_frame()
                image = frame_info[0]
                fps = frame_info[1]
                rectangle_list = frame_info[4]

            status = "loading"

            # decode binary to utf-8 when image is not None
            if image is not None:
                status = "ok"
                image = base64.b64encode(image).decode('utf-8')

            return {'type': media_type, 'image':image, 'fps':fps, 'status':status, 'rectangle_list':rectangle_list}
        else:
            return {'type': 'unkown', 'image':None, 'fps':0, 'status':'loading'}

# pylint: disable=abstract-method
class BaseHandler(tornado.web.RequestHandler):
    """
    base handler.
    """

# pylint: disable=abstract-method
class HomeHandler(BaseHandler):
    """
    handler index request
    """

    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        """
        handle home or index request only for get
        """
        self.render("home.html", listret=G_WEBAPP.list_channels())

# pylint: disable=abstract-method
class AddHandler(BaseHandler):
    """
    handler add request
    """
    @tornado.web.asynchronous
    def post(self, *args, **kwargs):
        """
        handle reqeust for add channel
        """
        channel_name = self.get_argument('name', '')
        self.finish(G_WEBAPP.add_channel(channel_name))

# pylint: disable=abstract-method
class DelHandler(BaseHandler):
    """
    handler delete request
    """
    @tornado.web.asynchronous
    def post(self, *args, **kwargs):
        """
        handel requst for delete channel
        """
        channel_name = self.get_argument('name', '')
        self.finish(G_WEBAPP.del_channel(channel_name))


# pylint: disable=abstract-method
class ViewHandler(BaseHandler):
    """
    handler view request
    """
    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        """
        handler request for view channel
        """
        channel_name = self.get_argument('name', '')
        if G_WEBAPP.is_channel_exists(channel_name):
            req_id = str(random.random())
            G_WEBAPP.add_requst((req_id, channel_name))
            self.render('view.html', channel_name=channel_name, req=req_id)
        else:
            raise tornado.web.HTTPError(404)


class WebSocket(tornado.websocket.WebSocketHandler):
    """
    web socket for web page socket quest
    """
    def open(self, *args, **kwargs):
        """
        called when client request by ws or wss
        """

        self.req_id = self.get_argument("req", '', True)
        self.channel_name = self.get_argument("name", '', True)

        # check request valid or not.
        if not G_WEBAPP.has_request((self.req_id, self.channel_name)):
            self.close()


    @staticmethod
    def send_message(obj, message, binary=False):
        """
        send message to client.
        """

        # check socket exist or not
        if not obj.ws_connection or not obj.ws_connection.stream.socket:
            return False

        ret = False
        try:
            obj.write_message(message, binary)
            ret = True
        except tornado.websocket.WebSocketClosedError:
            ret = False

        return ret


    def on_close(self):
        """
        called when closed web socket
        """

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def on_message(self, message):
        """
         On recv message from client.
        """
        if message == "next":
            self.run_task()


    def run_task(self):
        """
        send image to client
        """

        # check channel valid
        if not G_WEBAPP.is_channel_exists(self.channel_name) or \
           not G_WEBAPP.has_request((self.req_id, self.channel_name)):
            self.close()
            return

        result = G_WEBAPP.get_media_data(self.channel_name)

        # sleep 100ms if status not ok for frequently query
        if result['status'] != 'ok':
            time.sleep(0.1)



        # if channel not exist close websocket.
        if result['status'] == "error":
            self.close()
        # send message to client
        else:
            # close websoket when send failed or for image channel.
            ret = WebSocket.send_message(self, result)
            if not ret or result['type'] == "image":
                self.close()



def get_webapp():
    """
    start web applicatioin
    """
    # get template file and static file path.
    templatepath = os.path.join(config_parser.ConfigParser.get_rootpath(), "ui/templates")
    staticfilepath = os.path.join(config_parser.ConfigParser.get_rootpath(), "ui/static")

    # create application object.
    app = tornado.web.Application(handlers=[(r"/", HomeHandler),
                                            (r"/index", HomeHandler),
                                            (r"/add", AddHandler),
                                            (r"/del", DelHandler),
                                            (r"/view", ViewHandler),
                                            (r"/static/(.*)",
                                             tornado.web.StaticFileHandler,
                                             {"path": staticfilepath}),
                                            (r"/websocket", WebSocket)],
                                  template_path=templatepath)

    # create server
    http_server = tornado.httpserver.HTTPServer(app)

    return http_server


def start_webapp():
    """
    start webapp
    """
    http_server = get_webapp()
    config = config_parser.ConfigParser()
    http_server.listen(config.web_server_port, address=config.web_server_ip)

    print("Please visit http://" + config.web_server_ip + ":" +
          str(config.web_server_port) + " for whenet")
    tornado.ioloop.IOLoop.instance().start()


def stop_webapp():
    """
    stop web app
    """
    tornado.ioloop.IOLoop.instance().stop()

global G_WEBAPP
G_WEBAPP = WebApp()