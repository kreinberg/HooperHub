#!/usr/bin/env python3

""" Executable used to run the training process """

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import pickle
import tensorflow as tf
from hooperhub.seq2seq_model import Seq2SeqModel
from hooperhub.util import data_utils


tf.app.flags.DEFINE_integer("source_vocab_size", 1100,
                            "Input vocabulary size.")
tf.app.flags.DEFINE_integer("target_vocab_size", 200,
                            "Output vocabulary size.")
tf.app.flags.DEFINE_integer("size", "512", "Size of each model layer")
tf.app.flags.DEFINE_integer("batch_size", "50", "Size of each training batch")
tf.app.flags.DEFINE_float("learn_rate", 0.001, "Learning rate.")
tf.app.flags.DEFINE_string("data_dir", ".", "Training directory")
tf.app.flags.DEFINE_integer("batches_per_epoch", 500,
                            "Number of batches in an epoch")
tf.app.flags.DEFINE_string("training_filename", "training.tsv",
                           "Name of the training file")

FLAGS = tf.app.flags.FLAGS


def read_data(source_path, target_path):
  """ A generator for training data to be batched
    Args:
      source_path: Path for the source data.
      target_path: Path for the target data.
    Returns:
      Yields a tuple for both the source target data, which are
      stored in lists.
  """
  source_file = open(source_path, 'r')
  target_file = open(target_path, 'r')
  source_line = "x"
  target_line = "x"
  while source_line != "" and target_line != "":
    try:
      source_line = source_file.readline().strip()
      source_line = list(map(eval, source_line.split()))
      target_line = target_file.readline().strip()
      target_line = list(map(eval, target_line.split()))
      yield (source_line, target_line)
    except:
      print('Out of data.')
      raise StopIteration


def create_model(sess):
  """ Creates a Seq2SeqModel and uploads previously saved parameters if
      they exist.
      Args:
        sess: The tf.Session() object used in training.
      Returns:
        The Seq2SeqModel used for training.
  """
  model = Seq2SeqModel(FLAGS.source_vocab_size,
                       FLAGS.target_vocab_size,
                       FLAGS.size,
                       FLAGS.batch_size,
                       FLAGS.learn_rate)
  ckpt = tf.train.get_checkpoint_state(FLAGS.data_dir)
  if ckpt and tf.train.checkpoint_exists(ckpt.model_checkpoint_path):
    print("Created model with previously saved parameters.")
    model_meta_graph = os.path.join(FLAGS.data_dir, 'model.ckpt.meta')
    restorer = tf.train.import_meta_graph(model_meta_graph)
    restorer.restore(sess, tf.train.latest_checkpoint(FLAGS.data_dir))
  else:
    print("Created model with new parameters.")
    sess.run(tf.global_variables_initializer())
  return model


def id2token(data, id2vocab):
  """ Translates a numpy array of id's to tokens. This is not necessary for
      training, but can help visualize the sample input/predicted targets.
      Args:
        data: A numpy array containing token id's.
        source_data: A boolean representing if we should use source vocabulary
          or not.
      Returns:
        A list containing the words that were represented by the given id's.
  """
  token_list = []
  for _id in data:
    token_list.append(id2vocab[_id])
  return token_list


def main(_):
  """ Main function for the trainer. """
  source_training_path = os.path.join(FLAGS.data_dir, 'training.in')
  target_training_path = os.path.join(FLAGS.data_dir, 'training.tgt')
  checkpoint_path = os.path.join(FLAGS.data_dir, 'model.ckpt')
  data_generator = read_data(source_training_path, target_training_path)
  id2source_path = os.path.join(FLAGS.data_dir, 'pkl/id2input.pkl')
  id2target_path = os.path.join(FLAGS.data_dir, 'pkl/id2target.pkl')
  id2source = pickle.load(open(id2source_path, 'rb'))
  id2target = pickle.load(open(id2target_path, 'rb'))
  with tf.Session() as sess:
    model = create_model(sess)
    curr_step = 0
    while True:
      try:
        source_data = []
        target_data = []
        for _ in range(FLAGS.batch_size):
          data = next(data_generator)
          source_data.append(data[0])
          target_data.append(data[1])
        # add EOS token and extra padding for the target data
        source_batch, source_batch_len = model.get_batch(source_data)
        target_batch, _ = model.get_batch(target_data)
        input_feed = {
          model.enc_inputs: source_batch,
          model.enc_inputs_len: source_batch_len,
          model.dec_targets: target_batch
        }
        model.step(sess, input_feed)
        if curr_step > 0 and curr_step % FLAGS.batches_per_epoch == 0:
          print("Epoch: {}, Batch: {}".format(
                   curr_step//FLAGS.batches_per_epoch,
                   curr_step))
          print("Minibatch loss: {}".format(
                   sess.run(model.loss, input_feed)))
          print("Sample data")
          predict = model.make_prediction(sess, input_feed)
          samples = list(enumerate(zip(input_feed[model.enc_inputs].T,
                                       predict.T)))[:3]
          for i, (inp, pred) in samples:
            inp_tokens = id2token(inp, id2source)
            pred_tokens = id2token(pred, id2target)
            print("  Sample {}:".format(i+1))
            for a,b in zip(inp_tokens, pred_tokens):
              pass
              print("{: >20}  {: <20}".format(a,b))
          model.saver.save(sess, checkpoint_path)
          print()
        curr_step += 1
      except:
        print("Training ended.")
        break
    model.saver.save(sess, checkpoint_path)


if __name__ == '__main__':
  training_file_path = os.path.join(FLAGS.data_dir, FLAGS.training_filename)
  data_utils.data_to_token_ids(training_file_path)
  tf.app.run()


