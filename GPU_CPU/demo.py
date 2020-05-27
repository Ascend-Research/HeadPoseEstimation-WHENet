import numpy as np
import cv2
from whenet import WHENet
from utils import draw_axis

def crop_and_pred(img_path, bbox, model):
    img = cv2.imread(img_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    x_min, y_min, x_max, y_max = bbox
    img_rgb = img_rgb[y_min:y_max, x_min:x_max]
    img_rgb = cv2.resize(img_rgb,(224,224))
    img_rgb = np.expand_dims(img_rgb, axis=0)
    cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0,0,0), 1)
    yaw, pitch, roll = model.get_angle(img_rgb)
    draw_axis(img, yaw, pitch, roll, tdx=(x_min+x_max)/2, tdy=(y_min+y_max)/2, size = abs(x_max-x_min))
    cv2.imshow('output',img)
    cv2.waitKey(5000)

if __name__ == "__main__":
    model = WHENet('WHENet.h5')
    root = 'Sample/'
    print(model.model.summary())

    with open('Sample/bbox.txt', 'r') as f:
        lines = f.readlines()

    for l in lines:
        filename, bbox =l.split(',')
        bbox = bbox.split(' ')
        bbox = [int(b) for b in bbox]
        crop_and_pred(root+filename,bbox, model)