import numpy as np
import tensorflow as tf
from tensorflow.python.keras.backend import get_session
import os
import pickle
import time
from argparse import ArgumentParser
from multiprocessing import Process
import zmq
# from pyarrow import deserialize, serialize

tf.compat.v1.disable_eager_execution()

def mlp(x, hidden_sizes=(32,), activation=tf.tanh, output_activation=None):
    for h in hidden_sizes[:-1]:
        x = tf.keras.layers.Dense(x, units=h, activation=activation)
    return tf.keras.layers.Dense(x, units=hidden_sizes[-1], activation=output_activation)


def placeholder(dtype=tf.float32, shape=None):
    tf.compat.v1.disable_eager_execution()
    return tf.compat.v1.placeholder(dtype=dtype, shape=combined_shape(None, shape))

def combined_shape(length, shape=None):
    if shape is None:
        return (length,)
    return (length, shape) if np.isscalar(shape) else (length, *shape)

class GDModel():
    def __init__(self, observation_space, action_space, config=None, model_id='0', *args, **kwargs):
        with tf.compat.v1.variable_scope(model_id):
            self.x_ph = placeholder(shape=observation_space)
            self.x_ph = tf.compat.v1.placeholder(tf.float32, shape=)

        # 输出张量
        self.values = None
        self.scope = model_id

        # Initialize Tensorflow session
        self.sess = get_session()
        self.observation_space = observation_space
        self.action_space = action_space
        self.model_id = model_id
        self.config = config

        # 2. Build up model
        self.build()

        # Build assignment ops
        self._weight_ph = None
        self._to_assign = None
        self._nodes = None
        self._build_assign()

        # 参数初始化
        self.sess.run(tf.compat.v1.global_variables_initializer())    


    def set_weights(self, weights) -> None:
        feed_dict = {self._weight_ph[var.name]: weight
                     for (var, weight) in zip(tf.compat.v1.trainable_variables(scope=self.scope), weights)}
        self.sess.run(self._nodes, feed_dict=feed_dict)

    def _build_assign(self):
        self._weight_ph, self._to_assign = dict(), dict()
        variables = tf.compat.v1.trainable_variables(self.scope)
        for var in variables:
            self._weight_ph[var.name] = tf.compat.v1.placeholder(var.value().dtype, var.get_shape().as_list())
            self._to_assign[var.name] = var.assign(self._weight_ph[var.name])
        self._nodes = list(self._to_assign.values())

    def forward(self, x_batch):
        return self.sess.run(self.values, feed_dict={self.x_ph: x_batch})

    def build(self) -> None:
        with tf.compat.v1.variable_scope(self.scope):
            with tf.compat.v1.variable_scope('v'):
                self.values = mlp(self.x_ph, [512, 512, 512, 512, 512, 1], activation='tanh',
                                            output_activation=None)


model  = GDModel((567,), (5, 216))
with open('better_model3.ckpt', 'rb') as f:
    new_weights = pickle.load(f)
model.set_weights(new_weights)

print("successful")
