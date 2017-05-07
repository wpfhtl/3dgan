import tensorflow as tf
from tensorflow.contrib.layers import xavier_initializer as x_init
from tensorflow.contrib.layers import variance_scaling_initializer as he_init
from tensorflow.contrib.layers import batch_norm


def lrelu(x, leak=0.2, name='lrelu'):
    f1 = 0.5 * (1 + leak)
    f2 = 0.5 * (1 - leak)
    return f1 * x + f2 * abs(x)


def dense(x, input_size, output_size, name=None):
    w_name = name if name is None else name + '_w'
    b_name = name if name is None else name + '_b'
    W = tf.get_variable(name=w_name, shape=[input_size, output_size], initializer=he_init())
    # W = tf.Variable(tf.random_normal([input_size, output_size]))
    # b = tf.Variable(tf.random_normal([output_size]))
    b = tf.get_variable(name=b_name, shape=[output_size], initializer=he_init())
    return tf.matmul(x, W) + b
                        

def conv2d(x, input_size, output_size, ksize=3, stride=1, name=None):
    w_name = name if name is None else name + '_w'
    b_name = name if name is None else name + '_b'
    
    # if not name is None:
    K = tf.get_variable(name=w_name, shape=[ksize, ksize, input_size, output_size], initializer=he_init())
    b = tf.get_variable(name=b_name, shape=[output_size], initializer=he_init())
    # else:
    #     K = tf.Variable(tf.truncated_normal([ksize, ksize, input_size, output_size], stddev=0.1)) #, name=name))
    #     b = tf.Variable(tf.truncated_normal([output_size]))        
    h = tf.nn.conv2d(x, K, strides=[1, stride, stride, 1], padding='SAME')
    # return batch_norm(h+b)
    # print('created var', name)
    return h + b


def upsize(x, factor, output_size):
    input_shape = tf.shape(x)
    return tf.stack([input_shape[0], input_shape[1]*2, input_shape[2]*2, output_size])
    
    
def deconv2d(x, input_size, output_size, ksize=3, stride=2, name=None):
    w_name = name if name is None else name + '_w'
    b_name = name if name is None else name + '_b'
    K = tf.get_variable(name=w_name, shape=[ksize, ksize, output_size, input_size], initializer=he_init())
    b = tf.get_variable(name=b_name, shape=[output_size], initializer=he_init())
    
    # K = tf.Variable(tf.truncated_normal([ksize, ksize, output_size, input_size], stddev=0.1))
    h = tf.nn.conv2d_transpose(x, K, output_shape=upsize(x, 2, output_size), strides=[1, stride, stride, 1], padding='SAME')
    # b = tf.Variable(tf.truncated_normal([output_size]))
    return h + b


def flatten(x, name=None):
    input_shape = tf.shape(x)
    output_size = input_shape[1] * input_shape[2] * input_shape[3]
    return tf.reshape(x, [-1, output_size], name=name)



def L(x):
    """Mark this op as a layer."""
    tf.add_to_collection('layers', x)
    tf.summary.histogram(x.name, x)
    return x


def M(x, collection):
    """Mark this op as part of a collection and add histograms."""
    short_name = x.name.split('/')[-1]
    tf.add_to_collection(collection, x)
    tf.add_to_collection('batch_summaries', tf.summary.histogram(short_name, x))
    # print('Adding summary for', x)
    # print('Name:', x.name, 'Short Name:', short_name)
    return x



    
    
