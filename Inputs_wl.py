import tensorflow as tf
from tensorflow.python.framework import ops
from tensorflow.python.framework import dtypes
import os
import sys
import numpy as np
import math
import skimage
import skimage.io
from skimage.transform import rescale, resize, downscale_local_mean
from skimage.color import rgb2gray
import glob

IMAGE_HEIGHT = 360
IMAGE_WIDTH = 640
IMAGE_DEPTH = 3

NUM_CLASSES = 2
NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN = 191
NUM_EXAMPLES_PER_EPOCH_FOR_TEST = 40
NUM_EXAMPLES_PER_EPOCH_FOR_EVAL = 1


def _generate_image_and_label_batch(image, label, min_queue_examples,
                                    batch_size, shuffle):
    """Construct a queued batch of images and labels.

    Args:
      image: 3-D Tensor of [height, width, 3] of type.float32.
      label: 3-D Tensor of [height, width, 1] type.int32
      min_queue_examples: int32, minimum number of samples to retain
        in the queue that provides of batches of examples.
      batch_size: Number of images per batch.
      shuffle: boolean indicating whether to use a shuffling queue.

    Returns:
      images: Images. 4D tensor of [batch_size, height, width, 3] size.
      labels: Labels. 3D tensor of [batch_size, height, width ,1] size.
    """
    # Create a queue that shuffles the examples, and then
    # read 'batch_size' images + labels from the example queue.
    num_preprocess_threads = 1
    if shuffle:
        images, label_batch = tf.train.shuffle_batch(
            [image, label],
            batch_size=batch_size,
            num_threads=num_preprocess_threads,
            capacity=min_queue_examples + 3 * batch_size,
            min_after_dequeue=min_queue_examples)
    else:
        images, label_batch = tf.train.batch(
            [image, label],
            batch_size=batch_size,
            num_threads=num_preprocess_threads,
            capacity=min_queue_examples + 3 * batch_size)

    # Display the training images in the visualizer.
    # tf.image_summary('images', images)

    return images, label_batch


def CamVid_reader_seq(filename_queue, seq_length):
    image_seq_filenames = tf.split(
        axis=0, num_or_size_splits=seq_length, value=filename_queue[0])
    label_seq_filenames = tf.split(
        axis=0, num_or_size_splits=seq_length, value=filename_queue[1])

    image_seq = []
    label_seq = []
    for im, la in zip(image_seq_filenames, label_seq_filenames):
        imageValue = tf.read_file(tf.squeeze(im))
        labelValue = tf.read_file(tf.squeeze(la))
        image_bytes = tf.image.decode_png(imageValue)
        label_bytes = tf.image.decode_png(labelValue)
        image = tf.cast(tf.reshape(image_bytes, (IMAGE_HEIGHT,
                                                 IMAGE_WIDTH, IMAGE_DEPTH)), tf.float32)
        label = tf.cast(tf.reshape(
            label_bytes, (IMAGE_HEIGHT, IMAGE_WIDTH, 1)), tf.int64)
        image_seq.append(image)
        label_seq.append(label)
    return image_seq, label_seq


def CamVid_reader(filename_queue):

    image_filename = filename_queue[0]
    label_filename = filename_queue[1]

    imageValue = tf.read_file(image_filename)
    labelValue = tf.read_file(label_filename)

    image_bytes = tf.image.decode_png(imageValue)
    label_bytes = tf.image.decode_png(labelValue)

    image = tf.reshape(image_bytes, (IMAGE_HEIGHT, IMAGE_WIDTH, IMAGE_DEPTH))
    label = tf.reshape(label_bytes, (IMAGE_HEIGHT, IMAGE_WIDTH, 1))

    return image, label


def get_filename_list(dir_path):
    files = glob.glob(dir_path + "/*.png")
    print(files)
    image_filenames = []
    label_filenames = []

    for f in files:
        if "-annotation." in f:
            label_filenames.append(f)
        else:
            image_filenames.append(f)
    return image_filenames, label_filenames


def CamVidInputs(image_filenames, label_filenames, batch_size):

    images = ops.convert_to_tensor(image_filenames, dtype=dtypes.string)
    labels = ops.convert_to_tensor(label_filenames, dtype=dtypes.string)

    filename_queue = tf.train.slice_input_producer(
        [images, labels], shuffle=True)

    image, label = CamVid_reader(filename_queue)
    reshaped_image = tf.cast(image, tf.float32)

    min_fraction_of_examples_in_queue = 0.4
    min_queue_examples = int(NUM_EXAMPLES_PER_EPOCH_FOR_TRAIN *
                             min_fraction_of_examples_in_queue)
    print('Filling queue with %d CamVid images before starting to train. '
          'This will take a few minutes.' % min_queue_examples)

    # Generate a batch of images and labels by building up a queue of examples.
    return _generate_image_and_label_batch(reshaped_image, label,
                                           min_queue_examples, batch_size,
                                           shuffle=True)


def get_all_test_data(im_list, la_list):
    images = []
    labels = []
    index = 0
    for im_filename, la_filename in zip(im_list, la_list):
        im = skimage.io.imread(im_filename)
        im = resize(im, (im.shape[0] / 2, im.shape[1] / 2))
        # im = np.array(skimage.io.imread(im_filename), np.float32)
        im = np.array(im, np.float32)
        im = im[np.newaxis]
        # print(im.shape)

        la = skimage.io.imread(la_filename)
        la = rgb2gray(la)
        print(la.shape)
        la = resize(la, (la.shape[0] / 2, la.shape[1] / 2))
        la = la[np.newaxis]
        la = la[..., np.newaxis]
        print(la.shape)
        images.append(im)
        labels.append(la)
    return images, labels
