import numpy as np
import tensorflow as tf
from tensorflow.contrib.rnn import GRUCell


class Seq2SeqModel(object):
  """ A Seq2Seq model that utilizes high level functions from the TensorFlow
      1.0 API. The cell class is the GRU Cell from the Tensorflow contrib
      library. Much of the model is inspired by the tutorial provided by
      Google at https://tensorflow.org/tutorials/seq2seq.
  """

  def __init__(self,
               src_vocab_sz,
               tgt_vocab_sz,
               size,
               batch_size,
               learn_rate,
               train=True):
    """ Constructor for the Seq2SeqModel.
        Args:
          src_vocab_size: Number of source vocab tokens.
          tgt_vocab_size: Number of target vocab tokens.
          size: Size of each model layer.
          batch_size: Size of each training batch.
          learn_rate: Learning rate.
          train: Whether or not the model is for training.
    """
    self.PAD_ID = 0
    self.EOS_ID = 1
    self.src_vocab_sz = src_vocab_sz
    self.tgt_vocab_sz = tgt_vocab_sz
    self.embed_size = size
    self.enc_cell = GRUCell(size)
    self.dec_cell = GRUCell(size*2)
    self.train = train

    # Initialize placeholders
    self.enc_inputs = tf.placeholder(shape=(None,None),
                                     dtype=tf.int32,
                                     name="enc_inputs")
    self.enc_inputs_len = tf.placeholder(shape=(None,),
                                         dtype=tf.int32,
                                         name="enc_inputs_len")
    self.dec_targets = tf.placeholder(shape=(None,None),
                                      dtype=tf.int32,
                                      name="dec_targets")

    # Create embedding matrices
    self.src_embed_matrix = tf.Variable(tf.random_uniform(
                                        [self.src_vocab_sz, self.embed_size],
                                        1.0, 1.0), dtype=tf.float32)
    self.tgt_embed_matrix = tf.Variable(tf.random_uniform(
                                        [self.tgt_vocab_sz, self.embed_size],
                                        1.0, 1.0), dtype=tf.float32)

    # Prepare the encoder
    self.enc_inputs_embedded = tf.nn.embedding_lookup(self.src_embed_matrix,
                                                      self.enc_inputs)
    enc_outputs, enc_output_state = tf.nn.bidirectional_dynamic_rnn(
      cell_fw = self.enc_cell,
      cell_bw = self.enc_cell,
      inputs = self.enc_inputs_embedded,
      sequence_length = self.enc_inputs_len,
      dtype = tf.float32,
      time_major = True)
    self.enc_outputs = tf.concat(enc_outputs, 2)
    self.enc_state = tf.concat(enc_output_state, 1)

    # Prepare the decoder
    self.enc_max_time, self.batch_sz = tf.unstack(tf.shape(self.enc_inputs))
    self.dec_len = self.enc_inputs_len
    self.W = tf.Variable(tf.random_uniform([size*2, tgt_vocab_sz], -1, 1),
                         dtype=tf.float32)
    self.b = tf.Variable(tf.zeros([tgt_vocab_sz]), dtype=tf.float32)
    self.pad_slice = tf.zeros([self.batch_sz], dtype=tf.int32)
    self.eos_slice = tf.ones([self.batch_sz], dtype=tf.int32)
    self.pad_step_embedded = tf.nn.embedding_lookup(self.tgt_embed_matrix,
                                                    self.pad_slice)
    self.eos_step_embedded = tf.nn.embedding_lookup(self.tgt_embed_matrix,
                                                    self.eos_slice)
    def loop_fn(time, prev_output, prev_state, prev_loop_state):
      if prev_state == None:
        elems_finished = (0 >= self.dec_len)
        _input = self.eos_step_embedded
        cell_state = self.enc_state
        return (elems_finished,
                _input,
                cell_state,
                None,
                None)
      else:
        def get_next_input():
          out_logits = tf.add(tf.matmul(prev_output, self.W), self.b)
          pred = tf.argmax(out_logits, axis=1)
          return tf.nn.embedding_lookup(self.src_embed_matrix, pred)
        elems_finished = (time >= self.dec_len)
        finished_cond = tf.reduce_all(elems_finished)
        _input = tf.cond(finished_cond, lambda: self.pad_step_embedded,
                         get_next_input)
        cell_state = prev_state
        output = prev_output
        loop_state = None
        return (elems_finished,
                _input,
                cell_state,
                output,
                loop_state)

    self.loop_function = loop_fn
    dec_outputs_ta, dec_state, _ = tf.nn.raw_rnn(self.dec_cell, loop_fn)
    self.dec_outputs = dec_outputs_ta.stack()
    self.dec_state = dec_state
    dec_max_time, dec_batch_sz, dec_dim = tf.unstack(tf.shape(self.dec_outputs))
    dec_outputs_flat = tf.reshape(self.dec_outputs, (-1, dec_dim))
    dec_logits_flat = tf.add(tf.matmul(dec_outputs_flat, self.W), self.b)
    self.dec_logits = tf.reshape(dec_logits_flat,
                        (dec_max_time, dec_batch_sz, self.tgt_vocab_sz))
    self.dec_prediction = tf.argmax(self.dec_logits, 2)

    # Prepare the optimizer if training
    if self.train:
      stepwise_crossent = tf.nn.softmax_cross_entropy_with_logits(
                            labels=tf.one_hot(self.dec_targets,
                                              depth=self.tgt_vocab_sz,
                                              dtype=tf.float32),
                            logits=self.dec_logits)
      self.loss = tf.reduce_mean(stepwise_crossent)
      self.opt = tf.train.AdamOptimizer(learn_rate).minimize(self.loss)

    self.saver = tf.train.Saver(tf.global_variables())


  def get_batch(self, data):
    """ Gets a time major batch from data.
        Args:
          data: A 2D list of sentences.
        Returns:
          A time major numpy matrix and the lengths of each sentence.
    """
    batch_lens = [len(sentence) for sentence in data]
    batch_size = len(batch_lens)
    max_sentence_len = max(batch_lens)
    batch_major = np.zeros(shape=(batch_size, max_sentence_len),
                           dtype=np.int32)
    for i, sentence in enumerate(data):
      for j, elem in enumerate(sentence):
        batch_major[i, j] = elem
    time_major = batch_major.swapaxes(0, 1)
    return time_major, batch_lens


  def step(self, sess, input_feed):
    """ Runs a step in the model.
        Args:
          sess:  A session provided by the training program.
          input_feed: A dictionary containing the batch inputs and targets.
        Returns:
          The computed loss from training.
    """
    _, batch_loss = sess.run([self.opt, self.loss], input_feed)
    return batch_loss

  def make_prediction(self, sess, input_feed):
    """ Makes a target prediction in the model
        Args:
          sess: A session provided by either the training program or lexer.
          input_feed: A dictionary containing the batch inputs.
        Returns:
          A prediction tensor containing the precicted output.
    """
    prediction = sess.run(self.dec_prediction, input_feed)
    return prediction



