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
"""Parameter Validation module"""
import logging

PORT_INTERVAL_BEGIN = 1024
PORT_INTERVAL_END = 49151

def validate_ip(ip_str):
    if ip_str == '0.0.0.0':
        logging.error("IP Addr \"0.0.0.0\" is illegal")
        print("IP Addr \"0.0.0.0\" is illegal")
        return False

    sep = ip_str.split('.')
    if len(sep) != 4:
        return False
    for i, x in enumerate(sep):
        try:
            int_x = int(x)
            if int_x < 0 or int_x > 255:
                logging.error("Illegal ip: %s", ip_str)
                print("Illegal ip: %s"%ip_str)
                return False
        except ValueError:
            logging.error("IP format error:%s", ip_str)
            print("IP format error:%s"%ip_str)
            return False
    return True

def validate_port(value_str):
    try:
        value = int(value_str)
        if value < PORT_INTERVAL_BEGIN or value > PORT_INTERVAL_END:
            logging.error("Illegal port: %d", value)
            print("Illegal port: %d"%value)
            return False
    except ValueError:
        logging.error("Port format error:%s", value_str)
        print("Port format error:%s"%value_str)
        return False
    return True

def validate_integer(value_str, begin, end):
    try:
        value = int(value_str)
        if value < begin or value > end:
            return False
    except ValueError:
        return False
    return True

def Integer_greater(value_str, compared_value):
    try:
        value = int(value_str)
        if value < compared_value:
            return False
    except ValueError:
        return False
    return True

def validate_float(value_str, begin, end):
    try:
        value = float(value_str)
        if value < begin or value > end:
            return False
    except ValueError:
        return False
    return True