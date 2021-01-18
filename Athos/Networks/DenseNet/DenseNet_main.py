'''

Authors: Nishant Kumar.

Copyright:
Copyright (c) 2018 Microsoft Research
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

'''

import numpy
import argparse
import os, sys, time
import tensorflow.compat.v1 as tf
import _pickle as pickle

import nets_factory
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'TFCompiler'))
import DumpTFMtData

model_name = 'densenet121'
num_classes = 1000
network_fn = nets_factory.get_network_fn(
        model_name,
        num_classes=num_classes,
        is_training=False)

imagesPlaceHolder = tf.placeholder(tf.float32, shape=(None, 224, 224, 3), name='input_x')
logits, end_points = network_fn(imagesPlaceHolder)
pred = tf.argmax(logits, 3)

# If want to run another file, uncomment the following and pass the preprocessed file which contains float values.
# with open('ImageNum_42677.inp', 'r') as ff:
#   line = ff.readline()
#   line = line.split()
#   imagesTemp = list(map(lambda x : float(x), line))
#   imagesTemp = numpy.reshape(imagesTemp, (224,224,3))

sampleImageFilePath = './SampleImages/n02109961_36_denseNet_preprocessed.pkl'
with open(sampleImageFilePath, 'rb') as ff:
  imagesTemp = pickle.load(ff)
images = numpy.zeros(shape=(1,224,224,3))
images[0] = imagesTemp
feed_dict = {imagesPlaceHolder : images}

def parseArgs():
  parser = argparse.ArgumentParser()

  parser.add_argument("--savePreTrainedWeightsInt", type=bool, default=False, help="savePreTrainedWeightsInt")
  parser.add_argument("--savePreTrainedWeightsFloat", type=bool, default=False, help="savePreTrainedWeightsFloat")
  parser.add_argument("--scalingFac", type=int, default=15, help="scalingFac")
  parser.add_argument("--runPrediction", type=bool, default=False, help="runPrediction")
  parser.add_argument("--saveImgAndWtData", type=bool, default=False, help="saveImgAndWtData")

  args = parser.parse_args()
  return args

args = parseArgs()

with tf.Session() as sess:
  sess.run(tf.global_variables_initializer())

  output_tensor = None
  gg = tf.get_default_graph()
  for node in gg.as_graph_def().node:
    # if node.name == 'densenet121/logits/BiasAdd':
    if node.name == 'ArgMax':
      output_tensor = gg.get_operation_by_name(node.name).outputs[0]

  assert(output_tensor is not None)
  optimized_graph_def = DumpTFMtData.save_graph_metadata(output_tensor, sess, feed_dict)

  if args.savePreTrainedWeightsInt or args.savePreTrainedWeightsFloat or args.runPrediction or args.saveImgAndWtData:
    modelPath = './PreTrainedModel/tf-densenet121.ckpt'
    saver = tf.train.Saver()
    saver.restore(sess, modelPath)

  predictions = None
  if args.runPrediction:
    print("*************** Starting Prediction****************")
    start_time = time.time()
    predictions = sess.run(output_tensor, feed_dict=feed_dict)
    end_time = time.time()
    print("*************** Done Prediction****************")

  print(predictions)

  if args.saveImgAndWtData:
    DumpTFMtData.dumpImgAndWeightsData2(sess, images[0], 'DenseNet_img_input.inp', args.scalingFac)

