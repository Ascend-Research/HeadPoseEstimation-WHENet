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

import threading
import select
import struct
import logging
import socket
from google.protobuf.message import DecodeError
import common.presenter_message_pb2 as pb2
from common.channel_manager import ChannelManager
from common.channel_handler import ChannelHandler

#read nothing from socket.recv()
SOCK_RECV_NULL = b''

# epool will return if no event coming in 1 s
EPOLL_TIMEOUT = 1

# it specifies the number of unaccepted connections that
# the system will allow before refusing new connections.
SOCKET_WAIT_QUEUE = 2

# message head length, include 4 bytes message total length
# and 1 byte message name length
MSG_HEAD_LENGTH = 5


class PresenterSocketServer():
    """a socket server communication with presenter agent.

    """
    def __init__(self, server_address):
        """
        Args:
            server_address: server listen address,
                            include an ipv4 address and a port.
        """

        # thread exit switch, if set true, thread must exit immediately.
        self.thread_exit_switch = False
        # message head length, include 4 bytes message total length
        # and 1 byte message name length
        self.msg_head_len = 5
        self._create_socket_server(server_address)

    def _create_socket_server(self, server_address):
        """
        create a socket server
        Args:
            server_address: server listen address,
                            include an ipv4 address and a port.
        """

        # Create a socket server.
        self._sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock_server.bind(server_address)
        self._sock_server.listen(SOCKET_WAIT_QUEUE)
        self._sock_server.setblocking(False)

        # Get server host name and port
        host, port = self._sock_server.getsockname()[:2]

        # Start presenter socket server thread.
        threading.Thread(target=self._server_listen_thread).start()

        # Display directly on the screen
        print('Presenter socket server listen on %s:%s\n' % (host, port))

    def set_exit_switch(self):
        """set switch True to stop presenter socket server thread."""
        self.thread_exit_switch = True

    def _read_socket(self, conn, read_len):
        '''
        Read fixed length data
        Args:
            conn: a socket connection
            read_len: read fix byte.
        Returns:
            ret: True or False
            buf: read fix byte buf.
        '''
        has_read_len = 0
        read_buf = SOCK_RECV_NULL
        total_buf = SOCK_RECV_NULL
        while has_read_len != read_len:
            try:
                read_buf = conn.recv(read_len - has_read_len)
            except socket.error:
                logging.error("socket %u exception:socket.error", conn.fileno())
                return False, None
            if read_buf == SOCK_RECV_NULL:
                return False, None
            total_buf += read_buf
            has_read_len = len(total_buf)

        return True, total_buf

    def _read_msg_head(self, sock_fileno, conns):
        '''
        Args:
            sock_fileno: a socket fileno
            conns: all socket connections which created by server.
        Returns:
            msg_total_len: total message length.
            msg_name_len: message name length.
        '''
        ret, msg_head = self._read_socket(conns[sock_fileno], self.msg_head_len)
        if not ret:
            logging.error("socket %u receive msg head null", sock_fileno)
            return None, None

        # in Struct(), 'I' is unsigned int, 'B' is unsigned char
        msg_head_data = struct.Struct('IB')
        (msg_total_len, msg_name_len) = msg_head_data.unpack(msg_head)
        msg_total_len = socket.ntohl(msg_total_len)

        return msg_total_len, msg_name_len

    def _read_msg_name(self, sock_fd, conns, msg_name_len):
        '''
        Args:
            sock_fd: a socket fileno
            conns: all socket connections which created by server.
            msg_name_len: message name length.
        Returns:
            ret: True or False
            msg_name: message name.
        '''
        ret, msg_name = self._read_socket(conns[sock_fd], msg_name_len)
        if not ret:
            logging.error("socket %u receive msg name null", sock_fd)
            return False, None
        try:
            msg_name = msg_name.decode("utf-8")
        except UnicodeDecodeError:
            logging.error("msg name decode to utf-8 error")
            return False, None

        return True, msg_name

    def _read_msg_body(self, sock_fd, conns, msg_body_len, msgs):
        '''
        Args:
            sock_fd: a socket fileno
            conns: all socket connections which created by server.
            msg_name_len: message name length.
            msgs: msg read from a socket
        Returns:
            ret: True or False
        '''
        ret, msg_body = self._read_socket(conns[sock_fd], msg_body_len)
        if not ret:
            logging.error("socket %u receive msg body null", sock_fd)
            return False
        msgs[sock_fd] = msg_body
        return True

    def _read_sock_and_process_msg(self, sock_fileno, conns, msgs):
        '''
        Args:
            sock_fileno: a socket fileno, return value of socket.fileno()
            conns: all socket connections registered in epoll
            msgs: msg read from a socket
        Returns:
            ret: True or False
        '''

        # Step1: read msg head
        msg_total_len, msg_name_len = self._read_msg_head(sock_fileno, conns)
        if msg_total_len is None:
            logging.error("msg_total_len is None.")
            return False

        # Step2: read msg name
        ret, msg_name = self._read_msg_name(sock_fileno, conns, msg_name_len)
        if not ret:
            return ret

        # Step3:  read msg body
        msg_body_len = msg_total_len - self.msg_head_len - msg_name_len
        if msg_body_len < 0:
            logging.error("msg_total_len:%u, msg_name_len:%u, msg_body_len:%u",
                          msg_total_len, msg_name_len, msg_body_len)
            return False
        ret = self._read_msg_body(sock_fileno, conns, msg_body_len, msgs)
        if not ret:
            return ret

        # Step4: process msg
        ret = self._process_msg(conns[sock_fileno], msg_name, msgs[sock_fileno])
        return ret

    def _process_epollin(self, sock_fileno, epoll, conns, msgs):
        '''
        Args:
            sock_fileno: a socket fileno, return value of socket.fileno()
            epoll: a set of select.epoll.
            conns: all socket connections registered in epoll
            msgs: msg read from a socket
        '''
        msgs[sock_fileno] = b''
        try:
            ret = self._read_sock_and_process_msg(sock_fileno, conns, msgs)
            if not ret:
                self._clean_connect(sock_fileno, epoll, conns, msgs)
        except socket.error:
            logging.error("receive socket error.")
            self._clean_connect(sock_fileno, epoll, conns, msgs)

    def _accept_new_socket(self, epoll, conns):
        '''
        Args:
            epoll: a set of select.epoll.
            conns: all socket connections registered in epoll
        '''
        try:
            new_conn, address = self._sock_server.accept()
            new_conn.setblocking(True)
            epoll.register(new_conn.fileno(), select.EPOLLIN | select.EPOLLHUP)
            conns[new_conn.fileno()] = new_conn
            logging.info("create new connection:client-ip:%s, client-port:%s, fd:%s",
                         address[0], address[1], new_conn.fileno())
        except socket.error:
            logging.error("socket.error exception when sock.accept()")

    def _server_listen_thread(self):
        """socket server thread, epoll listening all the socket events"""
        epoll = select.epoll()
        epoll.register(self._sock_server.fileno(), select.EPOLLIN | select.EPOLLHUP)
        try:
            conns = {}
            msgs = {}
            while True:
                # thread must exit immediately
                if self.thread_exit_switch:
                    break

                events = epoll.poll(EPOLL_TIMEOUT)
                # timeout, but no event come, continue waiting
                if not events:
                    continue

                for sock_fileno, event in events:
                    # new connection request from presenter agent
                    if self._sock_server.fileno() == sock_fileno:
                        self._accept_new_socket(epoll, conns)

                    # remote connection closed
                    # it means presenter agent exit withot close socket.
                    elif event & select.EPOLLHUP:
                        logging.info("receive event EPOLLHUP")
                        self._clean_connect(sock_fileno, epoll, conns, msgs)
                    # new data coming in a socket connection
                    elif event & select.EPOLLIN:
                        self._process_epollin(sock_fileno, epoll, conns, msgs)
                    # receive event not recognize
                    else:
                        logging.error("not recognize event %f", event)
                        self._clean_connect(sock_fileno, epoll, conns, msgs)

        finally:
            logging.info("conns:%s", conns)
            logging.info("presenter server listen thread exit.")
            epoll.unregister(self._sock_server.fileno())
            epoll.close()
            self._sock_server.close()


    def _process_heartbeat(self, conn):
        '''
        set heartbeat
        Args:
            conn: a socket connection
        Returns:
            True: set heartbeat ok.

        '''
        sock_fileno = conn.fileno()
        handler = self.channel_manager.get_channel_handler_by_fd(sock_fileno)
        if handler is not None:
            handler.set_heartbeat()

        return True

    def _process_open_channel(self, conn, msg_data):
        """
        Deserialization protobuf and process open_channel request
        Args:
            conn: a socket connection
            msg_data: a protobuf struct, include open channel request.

        Returns:

        protobuf structure like this:
         ----------------------------------------------
        |channel_name        |    string               |
        |----------------------------------------------
        |content_type        |    ChannelContentType   |
        |----------------------------------------------

        enum ChannelContentType {
            kChannelContentTypeImage = 0;
            kChannelContentTypeVideo = 1;
        }
        """
        request = pb2.OpenChannelRequest()
        response = pb2.OpenChannelResponse()

        try:
            request.ParseFromString(msg_data)
        except DecodeError:
            logging.error("ParseFromString exception: Error parsing message")
            channel_name = "unknown channel"
            return self._response_open_channel(conn, channel_name, response,
                                               pb2.kOpenChannelErrorOther)

        channel_name = request.channel_name

        # check channel name if exist
        if not self.channel_manager.is_channel_exist(channel_name):
            logging.error("channel name %s is not exist.", channel_name)
            # if channel is not exist, need to create the channel
            ret = self.channel_manager.register_one_channel(channel_name)
            if ret != ChannelManager.err_code_ok:
                logging.error("Create the channel %s failed!, and ret is %d", channel_name, ret)
                err_code =  pb2.kOpenChannelErrorOther
                self._response_open_channel(conn, channel_name, response, err_code)

        # check channel path if busy
        if self.channel_manager.is_channel_busy(channel_name):
            logging.error("channel path %s is busy.", channel_name)
            err_code = pb2.kOpenChannelErrorChannelAlreadyOpened
            return self._response_open_channel(conn, channel_name, response,
                                               err_code)

        # if channel type is image, need clean image if exist
        self.channel_manager.clean_channel_image(channel_name)

        if request.content_type == pb2.kChannelContentTypeImage:
            media_type = "image"
        elif request.content_type == pb2.kChannelContentTypeVideo:
            media_type = "video"
        else:
            logging.error("media type %s is not recognized.",
                          request.content_type)
            return self._response_open_channel(conn, channel_name, response,
                                               pb2.kOpenChannelErrorOther)

        handler = ChannelHandler(channel_name, media_type)
        self.channel_manager.create_channel_resource(
            channel_name, conn.fileno(), media_type, handler)

        return self._response_open_channel(conn, channel_name, response,
                                           pb2.kOpenChannelErrorNone)

    def _response_open_channel(self, conn, channel_name, response, err_code):
        """
        Assemble protobuf to response open_channel request
        Args:
            conn: a socket connection
            channel_name: name of a channel.
            response: a protobuf response to presenter agent
            err_code: part of the response

        Returns:
            ret_code:True or False

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
        |error_code       |    enum          |    OpenChannelErrorCode     |
        |-------------------------------------------------------------------
        |error_message    |    string        |    xx bytes                 |
        |-------------------------------------------------------------------

        enum OpenChannelErrorCode {
            kOpenChannelErrorNone = 0;
            kOpenChannelErrorNoSuchChannel = 1;
            kOpenChannelErrorChannelAlreadyOpened = 2;
            kOpenChannelErrorOther = -1;
        }
        """
        response.error_code = err_code
        ret_code = False
        if err_code == pb2.kOpenChannelErrorNoSuchChannel:
            response.error_message = "channel {} not exist." \
                                        .format(channel_name)
        elif err_code == pb2.kOpenChannelErrorChannelAlreadyOpened:
            response.error_message = "channel {} is busy.".format(channel_name)
        elif err_code == pb2.kOpenChannelErrorNone:
            response.error_message = "open channel succeed"
            ret_code = True
        else:
            response.error_message = "Unknown err open channel {}." \
                                        .format(channel_name)

        self.send_message(conn, response, pb2._OPENCHANNELRESPONSE.full_name)
        return ret_code

    def send_message(self, conn, protobuf, msg_name):
        '''
        API for send message
        Args:
            conn: a socket connection.
            protobuf: message body defined in protobuf.
            msg_name: msg name.
        Returns: NA
        '''
        message_data = protobuf.SerializeToString()
        message_len = len(message_data)

        msg_name_size = len(msg_name)
        msg_total_size = self.msg_head_len + msg_name_size + message_len
        # in Struct(), 'I' is unsigned int, 'B' is unsigned char
        s = struct.Struct('IB')
        msg_head = (socket.htonl(msg_total_size), msg_name_size)
        packed_msg_head = s.pack(*msg_head)
        msg_data = packed_msg_head + \
            bytes(msg_name, encoding="utf-8") + message_data
        conn.sendall(msg_data)
