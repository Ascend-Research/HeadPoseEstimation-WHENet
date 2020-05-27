WHENet: Real-time Fine-Grained Estimation for Wide Range Head Pose
===
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

## Implementation
We provide both the Huawei Ascend processor and CPU/GPU implementation in the repository.
* [**Huawei Ascend implementation**]()
* [**CPU/GPU implementation**]()

## Experiment results
<img src=readme_imgs/video.gif height="220"/> <img src=readme_imgs/turn.JPG height="220"/> 
