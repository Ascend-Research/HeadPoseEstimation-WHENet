import hiai

from hiai.nn_tensor_lib import DataType
from atlasutil.presenteragent.presenter_types import *
import atlasutil
import numpy as np
import cv2
import os
import copy

from atlasutil import camera, ai, presenteragent, dvpp_process
from yolov3.yolov3 import *
from whenet.whenet import *

def main(): 

    #read image
    image = cv2.imread('test_img/test.jpg')
    image_height, image_width = image.shape[0], image.shape[1]
    presenter_config = './whenet.conf'
    
    # create graph for yolo_v3 and WHENet
    yolo_v3 = YOLOV3(image_height, image_width)
    whenet = WHENet(image_height, image_width)

    # convert image to RGB 
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
     # yolov3: preprocessing, transpose, inference, postprocessing
    nparryList, boxList  = yolo_v3.inference(image)

    # plot yolo and whenet result in the image
    save_img = 1
    if save_img:
        image_res = copy.deepcopy(image)
    # whenet: preprocessing, transpose, inference, postprocessing
    detection_result_list = []

    for i in range(len(nparryList)):

        box_width, box_height = (boxList[i][0]+boxList[i][1])/2, (boxList[i][2]+boxList[i][3])/2

        detection_item = whenet.inference(nparryList[i], box_width, box_height, presenter_flag=False)

        if save_img:
            
            #plot box for yolo
            cv2.rectangle(image_res, (boxList[i][0],boxList[i][2]), (boxList[i][1],boxList[i][3]), (127,125,125), 2)
            #plot lines for whenet
            cv2.line(image_res, (int(box_width), int(box_height)), (int(detection_item[0]),int(detection_item[1])),(255,0,0),4)
            cv2.line(image_res, (int(box_width), int(box_height)), (int(detection_item[2]),int(detection_item[3])),(0,255,0),4)
            cv2.line(image_res, (int(box_width), int(box_height)), (int(detection_item[4]),int(detection_item[5])),(0,0,255),4)

    if save_img:
        image_res = cv2.cvtColor(image_res, cv2.COLOR_RGB2BGR)
        cv2.imwrite("./test_img/test_output.jpg", image_res)


if __name__ == "__main__":
    main()    
    


