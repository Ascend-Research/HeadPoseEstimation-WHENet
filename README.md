WHENet: Real-time Fine-Grained Estimation for Wide Range Head Pose
===
**Yijun Zhou and James Gregson - BMVC2020**


**Abstract:** We present an end-to-end head-pose estimation network designed to predict Euler
angles through the full range head yaws from a single RGB image. Existing methods
perform well for frontal views but few target head pose from all viewpoints. This has
applications in autonomous driving and retail. Our network builds on multi-loss approaches
with changes to loss functions and training strategies adapted to wide range
estimation. Additionally, we extract ground truth labelings of anterior views from a
current panoptic dataset for the first time. The resulting Wide Headpose Estimation Network
(WHENet) is the first fine-grained modern method applicable to the full-range of
head yaws (hence wide) yet also meets or beats state-of-the-art methods for frontal head
pose estimation. Our network is compact and efficient for mobile devices and applications. [**ArXiv**](https://arxiv.org/abs/2005.10353)

## Demo
We provided two use case of the WHENet, image input and video input in this repo. Please make sure you installed all the requirments before running the demo code by `pip install -r requirements.txt`. Additionally, please download the [YOLOv3](https://drive.google.com/file/d/1wGrwu_5etcpuu_sLIXl9Nu0dwNc8YXIH/view?usp=sharing) model for head detection and put it under `yolo_v3/data`.

<img src=readme_imgs/video.gif height="220"/> <img src=readme_imgs/turn.JPG height="220"/> 

## Image demo
To run WHENet with image input, please put images and bbox.txt under one folder (E.g. Sample/) and just run `pthon demo.py`.

Format of bbox.txt are showed below:
```
image_name,x_min y_min x_max y_max
mov_001_007585.jpeg,240 0 304 83
```

## Video/Webcam demo
We used [YOLO_v3](https://github.com/qqwweee/keras-yolo3) in the video demo to get the cropped head image. 
In order to customize some of the functions we have put the yolo implementation and the pre-trained model in the repo.
[Hollywood head](https://www.di.ens.fr/willow/research/headdetection/) and [Crowdhuman](https://www.crowdhuman.org/) are used to train the head detection YOLO model. 
````
demo_video.py [--video INPUT_VIDEO_PATH] [--snapshot WHENET_MODEL] [--display DISPLAY_OPTION] 
              [--score YOLO_CONFIDENCE_THRESHOLD] [--iou IOU_THRESHOLD] [--gpu GPU#] [--output OUTPUT_VIDEO_PATH]
````
Please set `--video ''` for webcam input. 

## Dependncies
* EfficientNet https://github.com/qubvel/efficientnet
* Yolo_v3 https://github.com/qqwweee/keras-yolo3
