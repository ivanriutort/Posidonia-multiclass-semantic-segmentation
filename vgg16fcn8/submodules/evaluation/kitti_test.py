#!/usr/bin/env python
# pylint: disable=missing-docstring
# -*- coding: utf-8 -*-

"""Trains, evaluates and saves the model network using a queue."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import imp
import json
import logging
import numpy as np
import os.path
import sys

import scipy as scp
import scipy.misc


sys.path.insert(1, '../../incl')

import tensorflow as tf

import tensorvision.utils as utils
import tensorvision.core as core
import time as time


from seg_utils import seg_utils as seg
import utils.classes_utils as cutils

# configure logging
if 'TV_IS_DEV' in os.environ and os.environ['TV_IS_DEV']:
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO,
                        stream=sys.stdout)
else:
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO,
                        stream=sys.stdout)

flags = tf.app.flags
FLAGS = flags.FLAGS

# test_file = 'data_road/testing.txt'


def create_test_output(hypes, sess, image_pl, softmax, data_file):
    # data_dir = hypes['dirs']['data_dir']
    # data_file = os.path.join(data_dir, test_file)

    image_dir = os.path.dirname(data_file)

    logdir_green = "test_images_green/"

    logging.info("Images will be written to {}/test_images_{{green, rg}}"
                 .format(logdir_green))

    logdir_green = os.path.join(hypes['dirs']['output_dir'], logdir_green)

    if not os.path.exists(logdir_green):
        os.mkdir(logdir_green)

    image_list = []
    color_dict = cutils.get_output_color_dict(hypes)

    with open(data_file) as file:
        for i, image_file in enumerate(file):

            t = time.time()

            image_file = image_file.rstrip()
            image_file = os.path.join(image_dir, image_file)
            image = scp.misc.imread(image_file)
            shape = image.shape

            feed_dict = {image_pl: image}

            output = sess.run([softmax['softmax']], feed_dict=feed_dict)
            output_im = output[0].argmax(axis=1).reshape(shape[0], shape[1])
            output_prob = output[0].max(axis=1).reshape(shape[0], shape[1])

            # Saving RB Plot
            ov_image = seg.make_overlay(image, output_prob)
            name = os.path.basename(image_file)
            image_list.append((name, ov_image))

            new_name = name.split('.')[0] + '_green.png'

            green_image = utils.overlay_segmentation(image, output_im, color_dict)

            save_file = os.path.join(logdir_green, new_name)
            scp.misc.imsave(save_file, green_image)

            elapsed = time.time() - t
            print("elapsed time: " + str(elapsed))


def _create_input_placeholder():
    image_pl = tf.placeholder(tf.float32)
    label_pl = tf.placeholder(tf.float32)
    return image_pl, label_pl


def do_inference(logdir, data_file):
    """
    Analyze a trained model.

    This will load model files and weights found in logdir and run a basic
    analysis.

    Parameters
    ----------
    logdir : string
        Directory with logs.
    """
    hypes = utils.load_hypes_from_logdir(logdir)
    modules = utils.load_modules_from_logdir(logdir)

    # Tell TensorFlow that the model will be built into the default Graph.
    with tf.Graph().as_default():

        # prepare the tv session

        with tf.name_scope('Validation'):
            image_pl, label_pl = _create_input_placeholder()
            image = tf.expand_dims(image_pl, 0)
            softmax = core.build_inference_graph(hypes, modules, image=image)

        sess = tf.Session()
        saver = tf.train.Saver()

        core.load_weights(logdir, sess, saver)

        create_test_output(hypes, sess, image_pl, softmax, data_file)
    return


def main(_):

    """Run main function."""
    if FLAGS.logdir is None:
        logging.error("No logdir are given.")
        logging.error("Usage: tv-analyze --logdir dir")
        exit(1)

    if FLAGS.gpus is None:
        if 'TV_USE_GPUS' in os.environ:
            if os.environ['TV_USE_GPUS'] == 'force':
                logging.error('Please specify a GPU.')
                logging.error('Usage tv-train --gpus <ids>')
                exit(1)
            else:
                gpus = os.environ['TV_USE_GPUS']
                logging.info("GPUs are set to: %s", gpus)
                os.environ['CUDA_VISIBLE_DEVICES'] = gpus
    else:
        logging.info("GPUs are set to: %s", FLAGS.gpus)
        os.environ['CUDA_VISIBLE_DEVICES'] = FLAGS.gpus

    utils.load_plugins()

    logdir = os.path.realpath(FLAGS.logdir)

    logging.info("Starting to analyze Model in: %s", logdir)
    do_inference(logdir)



if __name__ == '__main__':
    tf.app.run()

