import hiai
from atlasutil import ai
from yolov3.yolov3_postprocessing import *
import numpy as np
import cv2
import copy
import os

class YOLOV3(object):
    def __init__(self, camera_height, camera_width):
        # create graph for YOLOV3
        self.yolo_v3 = ai.Graph('./model_om/yolo_model_v3_aipp.om')
       
        # # parameters for preprocessing
        self.ih, self.iw = (camera_height, camera_width)
        self.h, self.w = (416,416)
        self.scale = min(self.w/self.iw, self.h/self.ih)
        self.nw = int(self.iw*self.scale)
        self.nh = int(self.ih*self.scale)

        # parameters for postprocessing
        self.image_shape = [camera_height, camera_width]
        self.model_shape = [self.h, self.w]
        self.num_classes = 1
        self.anchors = self.get_anchors()
        

    def get_anchors(self):
        anchors_path = os.path.expanduser('./yolov3/yolo_anchors.txt')
        with open(anchors_path) as f:
            anchors = f.readline()
        anchors = [float(x) for x in anchors.split(',')]
        return np.array(anchors).reshape(-1, 2)


    def inference(self,img):
        # preprocessing: resize and paste input image to a new image with size 416*416
        img = np.array(img, dtype='float32')
        img_resize = cv2.resize(img, (self.nw,self.nh), interpolation=cv2.INTER_CUBIC)
        img_new = np.ones((416,416,3),np.float32) * 128
        img_new[(self.h-self.nh)//2:((self.h-self.nh)//2 + self.nh),(self.w-self.nw)//2:(self.w-self.nw)//2 + self.nw, :] = img_resize[:,:,:]

        # # inference
        # convert input data type to uint8 to meet requirements of AIPP
        img_new = img_new.astype(np.int8)  
        # inference: YOLO V3 with AIPP, AIPP will do the normalization for input image which is image = image/255.
        resultList = self.yolo_v3.Inference(img_new)
        
        # postprocessing
        # convert output data format from NCHW to NHWC

        res_0 = np.reshape(resultList[0], (1,18,13,13))
        out_0 = np.transpose(res_0, (0,2,3,1)).copy()

        res_1 = np.reshape(resultList[1], (1,18,26,26))
        out_1 = np.transpose(res_1, (0,2,3,1)).copy()
        
        res_2 = np.reshape(resultList[2], (1,18,52,52))
        out_2 = np.transpose(res_2, (0,2,3,1)).copy()

        out_list = [out_0, out_1, out_2]

        # convert yolo output to box axis and score
        box_axis, box_score = yolo_eval(out_list, self.anchors, self.num_classes, self.image_shape)
        
        # get the crop image and corresponding width/heigh info for WHENet
        nparryList, boxList = get_box_img(img, box_axis, box_score)
    
        return nparryList, boxList

