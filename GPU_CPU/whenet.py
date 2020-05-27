import efficientnet as efn
import keras
import numpy as np
from utils import softmax

class WHENet:
    def __init__(self, snapshot=None):
        base_model = efn.EfficientNetB0(include_top=False, input_shape=(224, 224, 3))
        out = base_model.output
        out = keras.layers.GlobalAveragePooling2D()(out)
        fc_yaw = keras.layers.Dense(name='yaw_new', units=120)(out) # 3 * 120 = 360 degrees in yaw
        fc_pitch = keras.layers.Dense(name='pitch_new', units=66)(out)
        fc_roll = keras.layers.Dense(name='roll_new', units=66)(out)
        self.model = keras.models.Model(inputs=base_model.input, outputs=[fc_yaw, fc_pitch, fc_roll])
        if snapshot!=None:
            self.model.load_weights(snapshot)
        self.idx_tensor = [idx for idx in range(66)]
        self.idx_tensor = np.array(self.idx_tensor, dtype=np.float32)
        self.idx_tensor_yaw = [idx for idx in range(120)]
        self.idx_tensor_yaw = np.array(self.idx_tensor_yaw, dtype=np.float32)

    def get_angle(self, img):
        mean = [0.485, 0.456, 0.406]
        std = [0.229, 0.224, 0.225]
        img = img/255
        img = (img - mean) / std
        predictions = self.model.predict(img, batch_size=8)
        yaw_predicted = softmax(predictions[0])
        pitch_predicted = softmax(predictions[1])
        roll_predicted = softmax(predictions[2])
        yaw_predicted = np.sum(yaw_predicted*self.idx_tensor_yaw, axis=1)*3-180
        pitch_predicted = np.sum(pitch_predicted * self.idx_tensor, axis=1) * 3 - 99
        roll_predicted = np.sum(roll_predicted * self.idx_tensor, axis=1) * 3 - 99
        return yaw_predicted, pitch_predicted, roll_predicted