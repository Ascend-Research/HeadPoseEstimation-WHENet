import hiai

from hiai.nn_tensor_lib import DataType
from atlasutil.presenteragent.presenter_types import *

import numpy as np
import cv2
import os

from atlasutil import camera, ai, presenteragent, dvpp_process
from yolov3.yolov3 import *
from whenet.whenet import *

def main(): 

    # camera settings
    camera_width = 1280
    camera_height = 720
    # presenter sever configuration
    presenter_config = './whenet.conf'
    cap = camera.Camera(id = 0, fps = 20, width = camera_width, height = camera_height , format = camera.CAMERA_IMAGE_FORMAT_YUV420_SP)
    
    if not cap.IsOpened():
        print("Open camera 0 failed")
        return

    dvpp_handle = dvpp_process.DvppProcess(camera_width, camera_height)

    # create graph for yolo_v3 and WHENet
    yolo_v3 = YOLOV3(camera_height, camera_width)
    whenet = WHENet(camera_height, camera_width)

    chan = presenteragent.OpenChannel(presenter_config)

    if chan == None:
        print("Open presenter channel failed")
        return

    while True:

        # read image from camera
        yuv_img = cap.Read()
        orig_image = dvpp_handle.Yuv2Jpeg(yuv_img)
        yuv_img = yuv_img.reshape((1080, 1280))
        image = cv2.cvtColor(yuv_img, cv2.COLOR_YUV2RGB_I420)
        
        # yolov3: obtain detected head area and corresponding location in the source image
        nparryList, boxList  = yolo_v3.inference(image)

        # whenet: obtain yaw pitch roll value and lines calculated based on those three angles 
        detection_result_list = []
  
        for i in range(len(nparryList)):
            box_width, box_height = (boxList[i][0]+boxList[i][1])/2, (boxList[i][2]+boxList[i][3])/2

            detection_item = whenet.inference(nparryList[i],  box_width, box_height)
            detection_result_list.extend(detection_item)

        # send result of WHENet to presentersever 
        chan.SendDetectionData(camera_width, camera_height, orig_image.tobytes(), detection_result_list)

if __name__ == "__main__":
    main()    
  


