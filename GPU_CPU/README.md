WHENet: Real-time Fine-Grained Estimation for Wide Range Head Pose
===
We provided two use case of the WHENet, image input and video input in this repo. Please make sure you installed all the requirments before running the demo code by `pip install -r requirements.txt`.
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

