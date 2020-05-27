import hiai

from timeit import default_timer as timer
import numpy as np
import cv2
import copy
import os
from math import cos, sin, pi

from atlasutil import ai
from atlasutil.presenteragent.presenter_types import *
from hiai.nn_tensor_lib import DataType

class WHENet(object):
    def __init__(self, camera_height, camera_width):
        self.whenet = ai.Graph('./model_om/whenet_aipp.om')
        self.camera_height = camera_height
        self.camera_width = camera_width

    def inference(self, nparryList, box_width, box_height, presenter_flag=True):
        '''
        WHENet preprocessing, inference and postprocessing

        Args: 
            nparryList: result from YOLO V3, which is detected head area
        Returns:
            If presenter_flag is True, return information(values and lines to be ploted) of yaw pitch roll to be sent to Presneter Sever
            else, return yaw pitch roll value values in numpy format
        '''

        # preprocessing, resize detected head area to 224*224 
        resized_image = cv2.resize(nparryList,(224,224))

        # convert input data type as unit8 to meet the requirement of AIPP
        whenet_input = resized_image.astype(np.uint8)

        # model with AIPP, AIPP will do the normalization for input image, which image = image/255.
        resultList_whenet = self.whenet.Inference(whenet_input)
        
        # postprocessing
        # convert model output to yaw pitch roll value
        yaw, pitch, roll = self.whenet_angle(resultList_whenet)

        # plot lines according to angles
        yaw_x, yaw_y, pitch_x, pitch_y, roll_x, roll_y = self.whenet_draw(yaw, pitch, roll, tdx=box_width, tdy=box_height, size = 200)

        # if presenter_flag is True, pack the yaw pitch roll value and corresponding axis as presenter sever 
        # required for sending. else, return source yaw pitch roll value

        if presenter_flag:
            # start point of lines to be ploted, located in the center of detected head 
            start_point_x = int(max(min(int(box_width), self.camera_width), 0))
            start_point_y = int(max(min(int(box_height), self.camera_height), 0))
            
            # ObjectDetectionResult() is pre-defined class for sending result to Presenter Sever
            # location of three lines and yaw pitch roll value will be sent
            info_yaw = ObjectDetectionResult()
            info_yaw.lt.x =  start_point_x
            info_yaw.lt.y =  start_point_y
            info_yaw.rb.x =  int(max(min(int(yaw_x), self.camera_width), 0)) 
            info_yaw.rb.y =  int(max(min(int(yaw_y), self.camera_height), 0))

            info_pitch = ObjectDetectionResult()
            info_pitch.lt.x =  start_point_x
            info_pitch.lt.y =  start_point_y
            info_pitch.rb.x =  int(max(min(int(pitch_x), self.camera_width), 0)) 
            info_pitch.rb.y =  int(max(min(int(pitch_y), self.camera_height), 0))

            info_roll = ObjectDetectionResult()
            info_roll.lt.x =  start_point_x
            info_roll.lt.y =  start_point_y
            info_roll.rb.x =  int(max(min(int(roll_x), self.camera_width), 0)) 
            info_roll.rb.y =  int(max(min(int(roll_y), self.camera_height), 0))

            info_yaw.result_text = str("yaw:") + ' ' + str(int(yaw))
            info_pitch.result_text = str("pitch:") + ' ' + str(int(pitch))
            info_roll.result_text = str("roll:") + ' '+ str(int(roll))
            
            return info_yaw,  info_pitch,  info_roll
        
        else: 
            return yaw_x, yaw_y, pitch_x, pitch_y, roll_x, roll_y


    def softmax(self, x):
        x -= np.max(x,axis=1, keepdims=True)
        a = np.exp(x)
        b = np.sum(np.exp(x), axis=1, keepdims=True)
        return a/b
        
    def whenet_draw(self, yaw, pitch, roll, tdx=None, tdy=None, size = 200):
        '''
        Plot lines based on yaw pitch roll values

        Args:
            yaw, pitch, roll: values of angles
            tdx, tdy: center of detected head area
            
        Returns:
            graph: locations of three lines
        '''
        #taken from hopenet
        pitch = pitch * np.pi / 180
        yaw = -(yaw * np.pi / 180)
        roll = roll * np.pi / 180

        tdx = tdx
        tdy = tdy
        
        # X-Axis pointing to right. drawn in red
        x1 = size * (cos(yaw) * cos(roll)) + tdx
        y1 = size * (cos(pitch) * sin(roll) + cos(roll) * sin(pitch) * sin(yaw)) + tdy

        # Y-Axis | drawn in green
        x2 = size * (-cos(yaw) * sin(roll)) + tdx
        y2 = size * (cos(pitch) * cos(roll) - sin(pitch) * sin(yaw) * sin(roll)) + tdy

        # Z-Axis (out of the screen) drawn in blue
        x3 = size * (sin(yaw)) + tdx
        y3 = size * (-cos(yaw) * sin(pitch)) + tdy
            
        return x1, y1, x2, y2, x3, y3

    def whenet_angle(self, resultList_whenet):
        '''
        Obtain yaw pitch roll value in degree based on the output of model
        
        Args:
            resultList_whenet: result of WHENet
            
        Returns:
            yaw_predicted, pitch_predicted, roll_predicted: yaw pitch roll values
        '''
        yaw = resultList_whenet[0]
        yaw = np.reshape(yaw, (1,120,1,1))
        yaw_out = np.transpose(yaw, (0,2,3,1)).copy()
        yaw_out = yaw_out.squeeze()
        yaw_out = np.expand_dims(yaw_out, axis=0) 

        pitch = resultList_whenet[1]
        pitch = np.reshape(pitch, (1,66,1,1))
        pitch_out = np.transpose(pitch, (0,2,3,1)).copy()
        pitch_out = pitch_out.squeeze()
        pitch_out = np.expand_dims(pitch_out, axis=0) 

        roll = resultList_whenet[2]
        roll = np.reshape(roll, (1,66,1,1))
        roll_out = np.transpose(roll, (0,2,3,1)).copy()
        roll_out = roll_out.squeeze()
        roll_out = np.expand_dims(roll_out, axis=0) 

        yaw_predicted = self.softmax(yaw_out)
        pitch_predicted = self.softmax(pitch_out)
        roll_predicted = self.softmax(roll_out)

        idx_tensor_yaw = [idx for idx in range(120)]
        idx_tensor_yaw = np.array(idx_tensor_yaw, dtype=np.float32)

        idx_tensor = [idx for idx in range(66)]
        idx_tensor = np.array(idx_tensor, dtype=np.float32)

        yaw_predicted = np.sum(yaw_predicted * idx_tensor_yaw, axis=1)*3-180
        pitch_predicted = np.sum(pitch_predicted * idx_tensor, axis=1) * 3 - 99
        roll_predicted = np.sum(roll_predicted * idx_tensor, axis=1) * 3 - 99
        
        return np.array(yaw_predicted), np.array(pitch_predicted), np.array(roll_predicted)


