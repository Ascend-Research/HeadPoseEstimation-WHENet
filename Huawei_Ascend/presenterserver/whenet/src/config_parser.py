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

"""whenet config parser module"""

import os
import configparser
import common.parameter_validation as validate

class ConfigParser():
    """ parse configuration from the config.conf"""
    __instance = None

    def __init__(self):
        """init"""

    def __new__(cls):
        """ensure class object is a single instance"""
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            cls.config_parser()
        return cls.__instance

    def config_verify(self):
        '''Verify configuration Parameters '''
        if not validate.validate_ip(ConfigParser.web_server_ip) or \
           not validate.validate_ip(ConfigParser.presenter_server_ip) or \
           not validate.validate_port(ConfigParser.web_server_port) or \
           not validate.validate_port(ConfigParser.presenter_server_port):
            return False
        return True

    @classmethod
    def config_parser(cls):
        """parser config from config.conf"""
        config_parser = configparser.ConfigParser()
        cls.root_path = ConfigParser.get_rootpath()
        config_file = os.path.join(cls.root_path, "config/config.conf")
        config_parser.read(config_file)
        cls.web_server_ip = config_parser.get('baseconf', 'web_server_ip')
        cls.presenter_server_ip = \
            config_parser.get('baseconf', 'presenter_server_ip')
        cls.web_server_port = config_parser.get('baseconf', 'web_server_port')
        cls.presenter_server_port = \
            config_parser.get('baseconf', 'presenter_server_port')


    @staticmethod
    def get_rootpath():
        """get presenter server's root directory."""
        path = __file__
        idx = path.rfind("src")

        return path[0:idx]
