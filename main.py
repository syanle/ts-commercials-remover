# coding:utf-8
from hlsdownloader_dynamic_encrypted import videoDownloader
import time, calendar, os, sys
from datetime import datetime, timedelta

try:
    import subprocess as commands
except ImportError:  # Python 2.x
    import commands

PYTHON_MAJOR_VERSION = sys.version_info

def dt2stamp(dt):
    hours_added = timedelta(hours = 8)
    # my given datetime is in beijing time
    dt -= hours_added
    # time.mktime should pass into localtime
    timestamp = calendar.timegm(dt.timetuple())
    return str(int(float(timestamp)*1000))

# videoUrl = "http://yd-vl.cztv.com/channels/lantian/channel006/720p.m3u8/1643974320000,1643976600000?a=1000"

def get_date():
    beijing_today = datetime.utcnow().date() + timedelta(hours = 8)
    return beijing_today

bj_today = get_date()

start_time = datetime(bj_today.year, bj_today.month, bj_today.day, 19, 32, 0, 0)
end_time = datetime(bj_today.year, bj_today.month, bj_today.day, 20, 10, 0, 0)

# change working dir to the script's dir
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# strftime must pass into str
if PYTHON_MAJOR_VERSION < (3,):
    # have to give the string in unicode and than encode
    # to escape from ascii taking over the conversion,
    # like "中文".decode('ascii') no matter #coding declaration 
    video_name_u = u"《钱塘老娘舅》"+start_time.strftime("%Y年%m月%d日").decode('utf-8')
    video_name = video_name_u.encode('utf-8')
else:
    video_name = "《钱塘老娘舅》"+start_time.strftime("%Y年%m月%d日")

# videoUrl = "http://yd-vl.cztv.com/channels/lantian/channel006/720p.m3u8/{},{}?a=1000".format(dt2stamp(start_time),dt2stamp(end_time))
# channel06 is another choice when channel006 is broken
# 06 is grabbed from http://tv.cztv.com/live1
# 006 is from http://www.cztv.com/live/ the latter one is in a more old-fasion style
videoUrl = "http://yd-vl.cztv.com/channels/lantian/channel06/720p.m3u8/{},{}?a=1000".format(dt2stamp(start_time),dt2stamp(end_time))
videoDownloader(videoUrl, video_name+'.ts')


# ads remover
from commercials_remover import *

template = cv2.imread('qiantanglaoniangjiu_logo_smallist.png',0)
template = template[0:15 , 0:40]
# [30,77,660,730] for searching into full logo
# frame_list = get_isads_list(video_name, template, [30,77,660,730], 0.6)
# [30,52,665,720] for only two words "qiantang", 0.6 will be all the wrong matches
frame_list = get_isads_list(video_name, template, [30,58,665,715], 0.7)

# trim ending
template_end = cv2.imread('end_logo.png',0)
cap = cv2.VideoCapture(video_name+".ts")
backward_index = len(frame_list)-1
cap.set(cv2.CAP_PROP_POS_FRAMES, backward_index)
success, bgr_image = cap.read()
while success and not is_ads(bgr_image, template_end, 0.7):
    backward_index -= 1
    print(backward_index)
    cap.set(cv2.CAP_PROP_POS_FRAMES, backward_index)
    success, bgr_image = cap.read()
    # only reverse check last 1/5 part
    if len(frame_list)-backward_index > len(frame_list)/5:
        break
frame_list = frame_list[:backward_index] + len(frame_list[backward_index:])*[1,]

frame_groups = extract_content_frames(smooth_and_compress2(frame_list))
print(frame_groups)
ffmpeg_command_single(video_name, frame_groups)


# YouTube uploader

def cur_file_dir():
     # get path of the script
     path = sys.path[0]
     # if the script is actually compiled from py2exe
     if os.path.isdir(path):
         return path
     elif os.path.isfile(path):
         return os.path.dirname(path)

def uploadVideo(ColumnTitle):
    cmd = 'youtube-upload --title="' + ColumnTitle + '" ' + os.path.join(cur_file_dir(), video_name + '.ts' + ' --client-secrets=client_secret_2017_jitoushan.json')
    print(cmd)
    uploadResult = commands.getstatusoutput(cmd)
    print("RESULT: ", uploadResult)
    if 'error' in uploadResult:
        # dateDeleter()
        print('Error found! Line deleting...')

# TODO: Youtube API requires audit these days
# uploadVideo(video_name)
