# for tensorflow 1.x
# (tested on tensorflow==1.15.4)
#
# refs
# efficientnet: https://github.com/qubvel/efficientnet
# whenet: https://github.com/Ascend-Research/HeadPoseEstimation-WHENet

from typing import List, NamedTuple, Tuple
import numpy as np
import tensorflow as tf


def softmax(x):
    x -= np.max(x,axis=1, keepdims=True)
    a = np.exp(x)
    b = np.sum(np.exp(x), axis=1, keepdims=True)
    return a/b


def swish(x):
    return x * tf.keras.activations.sigmoid(x)


class BlockArgs(NamedTuple):
    kernel_size: int
    num_repeat: int
    input_filters: int
    output_filters: int
    expand_ratio: int
    id_skip: bool
    se_ratio: float
    strides: List[int]

def SEBlock(block_args: BlockArgs):
    num_reduced_filters = max(1, int(block_args.input_filters * block_args.se_ratio))
    filters = block_args.input_filters * block_args.expand_ratio

    channel_axis = -1
    spatial_dims = [1, 2]

    def block(inputs):
        x = inputs
        x = tf.keras.layers.Lambda(lambda a: tf.keras.backend.mean(a, axis=spatial_dims, keepdims=True))(x)
        x = tf.keras.layers.Conv2D(num_reduced_filters, kernel_size=[1, 1], strides=[1, 1], padding="same", use_bias=True,)(x)
        x = swish(x)
        # Excite
        x = tf.keras.layers.Conv2D(filters, kernel_size=[1, 1], strides=[1, 1], padding="same", use_bias=True)(x)
        x = tf.keras.activations.sigmoid(x)
        out = tf.keras.layers.Multiply()([x, inputs])
        return out

    return block


def MBConvBlock(block_args: BlockArgs, momentum: float, epsilon: float, drop_connect_rate: float):
    batch_norm_momentum = momentum
    batch_norm_epsilon = epsilon

    channel_axis = -1
    spatial_dims = [1, 2]

    filters = block_args.input_filters * block_args.expand_ratio
    kernel_size = block_args.kernel_size

    def block(inputs):

        if block_args.expand_ratio != 1:
            x = tf.keras.layers.Conv2D(filters, kernel_size=[1, 1], strides=[1, 1], padding="same", use_bias=False,)(inputs)
            x = tf.keras.layers.BatchNormalization(axis=channel_axis, momentum=batch_norm_momentum, epsilon=batch_norm_epsilon)(x)
            x = swish(x)
        else:
            x = inputs

        x = tf.keras.layers.DepthwiseConv2D([kernel_size, kernel_size], strides=block_args.strides, padding="same", use_bias=False)(x)
        x = tf.keras.layers.BatchNormalization(axis=channel_axis, momentum=batch_norm_momentum, epsilon=batch_norm_epsilon)(x)
        x = swish(x)

        x = SEBlock(block_args)(x)

        x = tf.keras.layers.Conv2D(block_args.output_filters, kernel_size=[1, 1], strides=[1, 1], padding="same", use_bias=False)(x)
        x = tf.keras.layers.BatchNormalization(axis=channel_axis, momentum=batch_norm_momentum, epsilon=batch_norm_epsilon)(x)

        if (all(s == 1 for s in block_args.strides) and block_args.input_filters == block_args.output_filters):
            x = tf.keras.layers.Add()([x, inputs])
        return x

    return block


def construct_model(path_h5: str) -> tf.keras.models.Model:
    list_block_args = [
        BlockArgs(kernel_size=3, num_repeat=1, input_filters=32, output_filters=16, expand_ratio=1, id_skip=True, se_ratio=0.25, strides=[1, 1]),
        BlockArgs(kernel_size=3, num_repeat=2, input_filters=16, output_filters=24, expand_ratio=6, id_skip=True, se_ratio=0.25, strides=[2, 2]),
        BlockArgs(kernel_size=5, num_repeat=2, input_filters=24, output_filters=40, expand_ratio=6, id_skip=True, se_ratio=0.25, strides=[2, 2]),
        BlockArgs(kernel_size=3, num_repeat=3, input_filters=40, output_filters=80, expand_ratio=6, id_skip=True, se_ratio=0.25, strides=[2, 2]),
        BlockArgs(kernel_size=5, num_repeat=3, input_filters=80, output_filters=112, expand_ratio=6, id_skip=True, se_ratio=0.25, strides=[1, 1]),
        BlockArgs(kernel_size=5, num_repeat=4, input_filters=112, output_filters=192, expand_ratio=6, id_skip=True, se_ratio=0.25, strides=[2, 2]),
        BlockArgs(kernel_size=3, num_repeat=1, input_filters=192, output_filters=320, expand_ratio=6, id_skip=True, se_ratio=0.25, strides=[1, 1]),
    ]

    channel_axis = -1
    batch_norm_momentum=0.99
    batch_norm_epsilon=1e-3

    inputs = tf.keras.layers.Input(shape=(224, 224, 3))
    x = tf.keras.layers.Conv2D(filters=32, kernel_size=[3, 3], strides=[2, 2], padding="same", use_bias=False)(inputs)
    x = tf.keras.layers.BatchNormalization(axis=channel_axis, momentum=batch_norm_momentum, epsilon=batch_norm_epsilon)(x)
    x = swish(x)

    block_idx = 1
    n_blocks = sum([block_args.num_repeat for block_args in list_block_args])
    drop_rate = 0.2
    drop_rate_dx = drop_rate / n_blocks

    for block_args in list_block_args:
        x = MBConvBlock(block_args, batch_norm_momentum, batch_norm_epsilon, drop_connect_rate=drop_rate_dx * block_idx)(x)
        block_idx += 1

        if block_args.num_repeat > 1:
            block_args = block_args._replace(input_filters=block_args.output_filters, strides=[1, 1])

        for _ in range(block_args.num_repeat - 1):
            x = MBConvBlock(block_args, batch_norm_momentum, batch_norm_epsilon, drop_connect_rate=drop_rate_dx * block_idx)(x)
            block_idx += 1

    x = tf.keras.layers.Conv2D(filters=1280, kernel_size=[1, 1], strides=[1, 1], padding="same", use_bias=False,)(x)
    x = tf.keras.layers.BatchNormalization(axis=channel_axis, momentum=batch_norm_momentum, epsilon=batch_norm_epsilon)(x)
    x = swish(x)

    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    fc_yaw = tf.keras.layers.Dense(name='yaw_new', units=120)(x)
    fc_pitch = tf.keras.layers.Dense(name='pitch_new', units=66)(x)
    fc_roll = tf.keras.layers.Dense(name='roll_new', units=66)(x)

    outputs = [fc_yaw, fc_pitch, fc_roll]
    model = tf.keras.models.Model(inputs=inputs, outputs=outputs)
    model.load_weights(path_h5)
    return model


class WHENetTF:
    def __init__(self, path_h5: str):
        self.model = construct_model(path_h5)
        self.idx_tensor = [idx for idx in range(66)]
        self.idx_tensor = np.array(self.idx_tensor, dtype=np.float32)
        self.idx_tensor_yaw = [idx for idx in range(120)]
        self.idx_tensor_yaw = np.array(self.idx_tensor_yaw, dtype=np.float32)

    def get_angle(self, img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        mean = [0.485, 0.456, 0.406]
        std = [0.229, 0.224, 0.225]
        img = img / 255
        img = (img - mean) / std
        predictions = self.model.predict(img, batch_size=8)
        yaw_predicted = softmax(predictions[0])
        pitch_predicted = softmax(predictions[1])
        roll_predicted = softmax(predictions[2])
        yaw_predicted = np.sum(yaw_predicted * self.idx_tensor_yaw, axis=1) * 3-180
        pitch_predicted = np.sum(pitch_predicted * self.idx_tensor, axis=1) * 3 - 99
        roll_predicted = np.sum(roll_predicted * self.idx_tensor, axis=1) * 3 - 99
        return yaw_predicted, pitch_predicted, roll_predicted

    def save(self, dir_model: str):
        tf.saved_model.save(self.model, dir_model)
