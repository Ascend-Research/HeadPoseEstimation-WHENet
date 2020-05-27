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

"""presenter socket server module"""

import os
import logging
from logging.config import fileConfig
from google.protobuf.message import DecodeError
import common.presenter_message_pb2 as pb2
from common.channel_manager import ChannelManager
from common.presenter_socket_server import PresenterSocketServer
from whenet.src.config_parser import ConfigParser

class WhnetServer(PresenterSocketServer):
    '''A server for whenet'''
    def __init__(self, server_address):
        '''init func'''
        self.channel_manager = ChannelManager(["image", "video"])
        super(WhnetServer, self).__init__(server_address)

    def _clean_connect(self, sock_fileno, epoll, conns, msgs):
        """
        close socket, and clean local variables
        Args:
            sock_fileno: a socket fileno, return value of socket.fileno()
            epoll: a set of select.epoll.
            conns: all socket connections registered in epoll
            msgs: msg read from a socket
        """
        logging.info("clean fd:%s, conns:%s", sock_fileno, conns)
        self.channel_manager.clean_channel_resource_by_fd(sock_fileno)
        epoll.unregister(sock_fileno)
        conns[sock_fileno].close()
        del conns[sock_fileno]
        del msgs[sock_fileno]


    def _process_msg(self, conn, msg_name, msg_data):
        """
        Total entrance to process protobuf msg
        Args:
            conn: a socket connection
            msg_name: name of a msg.
            msg_data: msg body, serialized by protobuf

        Returns:
            False:somme error occured
            True:succeed

        """
        # process open channel request
        if msg_name == pb2._OPENCHANNELREQUEST.full_name:
            ret = self._process_open_channel(conn, msg_data)
        # process image request, receive an image data from presenter agent
        elif msg_name == pb2._PRESENTIMAGEREQUEST.full_name:
            ret = self._process_image_request(conn, msg_data)
        # process heartbeat request, it used to keepalive a channel path
        elif msg_name == pb2._HEARTBEATMESSAGE.full_name:
            ret = self._process_heartbeat(conn)
        else:
            logging.error("Not recognized msg type %s", msg_name)
            ret = False

        return ret

    def _response_image_request(self, conn, response, err_code):
        """
        Assemble protobuf to response image_request
        Message structure like this:
        --------------------------------------------------------------------
        |total message len   |    int         |    4 bytes                  |
        |-------------------------------------------------------------------
        |message name len    |    byte        |    1 byte                   |
        |-------------------------------------------------------------------
        |message name        |    string      |    xx bytes                 |
        |-------------------------------------------------------------------
        |message body        |    protobuf    |    xx bytes                 |
        --------------------------------------------------------------------

        protobuf structure like this:
        --------------------------------------------------------------------
        |error_code       |    enum          |    PresentDataErrorCode     |
        |-------------------------------------------------------------------
        |error_message    |    string        |    xx bytes                 |
        |-------------------------------------------------------------------

        enum PresentDataErrorCode {
            kPresentDataErrorNone = 0;
            kPresentDataErrorUnsupportedType = 1;
            kPresentDataErrorUnsupportedFormat = 2;
            kPresentDataErrorOther = -1;
        }
        """
        response.error_code = err_code
        ret_code = True
        if err_code == pb2.kPresentDataErrorUnsupportedFormat:
            response.error_message = "Present data not support format."
            logging.error("Present data not support format.")
            ret_code = False
        elif err_code == pb2.kPresentDataErrorNone:
            response.error_message = "Present data ok"
            ret_code = True
        else:
            response.error_message = "Present data not known error."
            logging.error("Present data not known error.")
            ret_code = False

        self.send_message(conn, response, pb2._PRESENTIMAGERESPONSE.full_name)
        return ret_code

    def _process_image_request(self, conn, msg_data):
        """
        Deserialization protobuf and process image_request
        Args:
            conn: a socket connection
            msg_data: a protobuf struct, include image request.

        Returns:

        protobuf structure like this:
         ------------------------------------
        |format        |    ImageFormat      |
        |------------------------------------
        |width         |    uint32           |
        |------------------------------------
        |height        |    uint32           |
        |------------------------------------
        |data          |    bytes            |
         ------------------------------------
        enum ImageFormat {
            kImageFormatJpeg = 0;
        }
        """
        request = pb2.PresentImageRequest()
        response = pb2.PresentImageResponse()

        # Parse msg_data from protobuf
        try:
            request.ParseFromString(msg_data)
        except DecodeError:
            logging.error("ParseFromString exception: Error parsing message")
            err_code = pb2.kPresentDataErrorOther
            return self._response_image_request(conn, response, err_code)

        sock_fileno = conn.fileno()
        handler = self.channel_manager.get_channel_handler_by_fd(sock_fileno)
        if handler is None:
            logging.error("get channel handler failed")
            err_code = pb2.kPresentDataErrorOther
            return self._response_image_request(conn, response, err_code)

        # Currently, image format only support jpeg
        if request.format != pb2.kImageFormatJpeg:
            logging.error("image format %s not support", request.format)
            err_code = pb2.kPresentDataErrorUnsupportedFormat
            return self._response_image_request(conn, response, err_code)

        rectangle_list = []
        if request.rectangle_list:
            for one_rectangle in request.rectangle_list:
                rectangle = []
                rectangle.append(one_rectangle.left_top.x)
                rectangle.append(one_rectangle.left_top.y)
                rectangle.append(one_rectangle.right_bottom.x)
                rectangle.append(one_rectangle.right_bottom.y)
                rectangle.append(one_rectangle.label_text)
                # add the detection result to list
                rectangle_list.append(rectangle)

        handler.save_image(request.data, request.width, request.height, rectangle_list)
        return self._response_image_request(conn, response,
                                            pb2.kPresentDataErrorNone)

    def stop_thread(self):
        channel_manager = ChannelManager([])
        channel_manager.close_all_thread()
        self.set_exit_switch()

def run():
    '''Entrance function of Whnet Server '''
    # read config file
    config = ConfigParser()

    # config log
    log_file_path = os.path.join(ConfigParser.root_path, "config/logging.conf")
    fileConfig(log_file_path)
    logging.getLogger('whenet')

    if not config.config_verify():
        return None

    logging.info("presenter server is starting...")
    server_address = (config.presenter_server_ip,
                      int(config.presenter_server_port))
    return WhnetServer(server_address)
