import tensorflow as tf
import numpy as np
from .model import Model
from .ops import dense, conv2d, deconv2d, lrelu, flatten, L



class VAEGAN(Model):
    def __init__(self, x, optimizer):
        Model.__init__(self)
        self.latent_size = 512
        self.batch_size = 256
        self._optimizer = optimizer
        
        # encoder
        self._encoder = self._build_encoder(x)
        # latent
        self._latent, self._z_mean, self._z_stddev = self._build_latent(self._encoder)
        # decoder
        self._decoder = self._build_decoder(self._latent)
        # loss
        generated_loss = -tf.reduce_sum(x * tf.log(1e-8 + self._decoder) + \
                                            (1 - x) * tf.log(1e-8 + (1 - self._decoder)))
        latent_loss = 0.5 * tf.reduce_sum(tf.square(self._z_mean) + \
                                              tf.square(self._z_stddev) - \
                                              tf.log(1e-8 + tf.square(self._z_stddev)) - 1)
        self._loss = tf.reduce_mean(generated_loss + latent_loss)
        self._generated_loss = tf.reduce_sum(generated_loss)
        self._latent_loss = tf.reduce_sum(latent_loss)

        self._discriminator = self._build_discriminator(x)
        
        

        # self._discriminator_real, self._discriminator_logits_real = self._build_discriminator(x)
        # self._discriminator_loss_real = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=self._discriminator_logits_real, labels=tf.ones_like(self._discriminator_real)))
        # self._discriminator_fake, self._discriminator_logits_fake = self._build_discriminator(self._decoder)
        # self._discriminator_loss_fake = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=self._discriminator_logits_fake, labels=tf.ones_like(self._discriminator_fake)))
        # self._discriminator_loss = self._discriminator_loss_real + self._discriminator_loss_fake



    def _build_discriminator(self, x):
        with tf.variable_scope('discriminator'):
            x = lrelu(conv2d(x, 3, 64, 5, 2))
            x = lrelu(conv2d(x, 64, 128, 5, 2))
            x = lrelu(conv2d(x, 128, 256, 5, 2))
            x = lrelu(conv2d(x, 256, 256, 5, 2))
            x = lrelu(conv2d(x, 256, 96, 32, 1))
            x = lrelu(conv2d(x, 96, 32, 1))
            x = flatten(x)
            
            out = tf.nn.sigmoid(x)
            tf.identity(out, name='sample')
        return out, x


    def _build_encoder(self, x):
        """Input: 64x64x3. Output: 4x4x32."""
        # layer_sizes = [64, 128, 256, 256, 96, 32] 
        with tf.variable_scope('encoder'):
            x = lrelu(conv2d(x, 3, 64, 5, 2))       ; L(x)
            x = lrelu(conv2d(x, 64, 128, 5, 2))     ; L(x)
            x = lrelu(conv2d(x, 128, 256, 5, 2))    ; L(x)
            x = lrelu(conv2d(x, 256, 256, 5, 2))    ; L(x)
            x = lrelu(conv2d(x, 256, 96, 1))        ; L(x)
            x = lrelu(conv2d(x, 96, 32, 1))         ; L(x)
            tf.identity(x, name='sample')
        return x

    
    def _build_latent(self, x):
        """Input: 4x4x32. Output: 200."""
        with tf.variable_scope('latent'):
            flat = flatten(x)
            z_mean = dense(flat, 32*4*4, self.latent_size)       ; L(z_mean)
            z_stddev = dense(flat, 32*4*4, self.latent_size)     ; L(z_stddev)
            samples = tf.random_normal([self.batch_size, self.latent_size], 0, 1, dtype=tf.float32)
            z = (z_mean + (z_stddev * samples))                  ; L(z)
            tf.identity(z, name='sample')
        return (z, z_mean, z_stddev)

    
    def _build_decoder(self, x):
        """Input: 200. Output: 64x64x3."""
        # layer sizes = [96, 256, 256, 128, 64]
        with tf.variable_scope('decoder'):
            x = dense(x, self.latent_size, 32*4*4)
            x = tf.reshape(x, [-1, 4, 4, 32]) # un-flatten
            
            x = tf.nn.relu(conv2d(x, 32, 96, 1))         ; L(x)
            x = tf.nn.relu(conv2d(x, 96, 256, 1))        ; L(x)
            x = tf.nn.relu(deconv2d(x, 256, 256, 5, 2))  ; L(x)
            x = tf.nn.relu(deconv2d(x, 256, 128, 5, 2))  ; L(x)
            x = tf.nn.relu(deconv2d(x, 128, 64, 5, 2))   ; L(x)
            x = tf.nn.sigmoid(deconv2d(x, 64, 3, 5, 2))  ; L(x)
            tf.identity(x, name='sample')
        return x

    def train(self, epoch, x_input, data, batch_size, tb_writer, summary_nodes, display=True):
        epoch_start_time = time.time()
        n_batches = int(data.train.num_examples/batch_size)
        for i in range(n_batches):
            xs, ys = data.train.next_batch(batch_size)
            _, l, summary = self._sess.run([self._train_op, self.loss, summary_nodes], feed_dict={x_input: xs})
            print_progress(epoch, batch_size*(i+1), data.train.num_examples, epoch_start_time, {'loss': l})
            tb_writer.add_summary(summary, epoch)

        # # perform validation
        # results = fold(self._sess, x_input, [self.loss], data.validation, batch_size, int(data.validation.num_examples/batch_size))
        # stdout.write(', validation: {:.4f}\r\n'.format(results[0]))
        stdout.write('\r\n')



    