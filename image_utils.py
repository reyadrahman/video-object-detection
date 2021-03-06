'''
Utility functions for preparing video frames
'''

from os.path import exists, join, dirname, abspath, splitext, basename
from os import system, listdir
from PIL import Image
import numpy as np
import cv2
import tempfile
import pylab
import re
from config import NUM_FIRST_FRAMES_SKIPPED, N_FRAMES

ROOT = dirname(abspath(__file__))

def get_prepared_images(url, ms_between_frames, video_filename, wnid=None):
  '''
  Returns:
    The  directory that contains the image frames.
    The image filenames take the format:
      <milliseconds_into_the_video>.jpg
    If wnid is None, the directory is stored in data/images.
    Else, the directory is stored in data/imagenet/<wnid>/annotated
    The image dir takes the format:
      <sanitized video url>_<milliseconds_between_frames>
  '''
  video_id = re.match('.*v=(.*$)', url).groups()[0]
  if wnid is None:
    image_dir = join(ROOT, 'data/images',
                     video_id + '_' + str(ms_between_frames))
  else:
    image_dir = join(ROOT, 'data/imagenet', wnid, 'prepared-video-frames',
                     video_id + '_' + str(ms_between_frames))
  if exists(image_dir):
    return image_dir
  system('mkdir -p ' + image_dir)
  return _prepare_images(video_filename, image_dir, ms_between_frames)

def _prepare_images(video_filename, image_dir, ms_between_frames):
  cap = cv2.VideoCapture(video_filename)
  frame_count = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
  frames_per_s = int(cap.get(cv2.cv.CV_CAP_PROP_FPS))

  step = (ms_between_frames / 1000) * frames_per_s
  # the first frame is usually blank, or a title screen
  image_count = NUM_FIRST_FRAMES_SKIPPED
  for i in range(frame_count)[step*NUM_FIRST_FRAMES_SKIPPED:step*N_FRAMES:step]:
    cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, i)
    retval, bgr_image = cap.read()
    filename = join(image_dir, str(image_count * ms_between_frames) + '.jpg')
    Image.fromarray(_prepare_image(bgr_image)).save(filename,
                                                   format='JPEG')
    image_count += 1
    print image_count, '/', frame_count/step
  return image_dir

def _prepare_image(bgr_image):
  'Resizes the images to 256x256'
  image = resize_and_paste(Image.fromarray(bgr_image), (256, 256))
  return np.asarray(image).astype(np.uint8)

def resize_and_paste(image, new_shape):
  '''
  The original image proportions are left unchanged; any left over area
  is filled with black.
  '''
  new_width, new_height = new_shape[:2]
  cw, ch = image.size
  # Even though the image is BGR, here RGB has the same effect
  result = Image.new('RGB', (new_width, new_height), color=(0,0,0))

  dw = float(new_width) / cw
  dh = float(new_height) / ch

  if dw < dh:
    ratio = float(new_width) / cw
    image = image.resize((int(cw * ratio), int(ch * ratio)))
    cw, ch = image.size
    result.paste(image, (0, (new_height - ch) / 2))
  else:
    ratio = float(new_height) / ch
    image = image.resize((int(cw * ratio), int(ch * ratio)))
    cw, ch = image.size
    result.paste(image, ((new_width - cw) / 2, 0))
  return result

def convert_bgr_to_rgb(image_filename, channel_order=(2,1,0)):
  image = np.asarray(Image.open(image_filename))
  image = image[:, :, channel_order]
  tmp = '/tmp/image-conversion'
  system('mkdir -p ' + tmp)
  tf = tempfile.NamedTemporaryFile(dir=tmp, delete=False)
  Image.fromarray(image).save(tf.name, format='JPEG')
  return tf.name

def show_image(image):
  pylab.imshow(image)
  pylab.show()

def ordered_listdir(image_dir):
  '''
  Returns a list of image basenames in `image_dir`, ordered numerically
  by name. e.g. 7.jpg is listed before 10.jpg.
  '''
  # skip the mac .DS_Store file
  filenames = [join(image_dir, x) for x in listdir(image_dir) if not x == '.DS_Store']
  return sorted(filenames, key=lambda x: int(splitext(basename(x))[0]))

