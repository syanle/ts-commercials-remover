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

videoUrl = "http://yd-vl.cztv.com/channels/lantian/channel006/720p.m3u8/1643974320000,1643976600000?a=1000"

def get_date():
    beijing_today = datetime.utcnow() + timedelta(hours = 8)
    return beijing_today.date()

# bj_today = get_date() - timedelta(days = 1)
bj_today = get_date()

start_time = datetime(bj_today.year, bj_today.month, bj_today.day, 19, 32, 0, 0)
end_time = datetime(bj_today.year, bj_today.month, bj_today.day, 20, 8, 35, 0)

# change working dir to the script's dir
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# strftime must pass into str
if PYTHON_MAJOR_VERSION < (3,):
    # have to give the string in unicode and than encode
    # to escape from ascii taking over the conversion,
    # like "中文".decode('ascii') no matter #coding declaration 
    # video_name_u = u"《钱塘老娘舅》"+start_time.strftime("%Y年%m月%d日").decode('utf-8')
    video_name_u = u"《钱塘老娘舅》"+start_time.strftime('%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日').decode('utf-8')
    video_name = video_name_u
else:
    # video_name = "《钱塘老娘舅》"+start_time.strftime("%Y年%m月%d日")
    video_name = "《钱塘老娘舅》"+start_time.strftime('%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')

# videoUrl = "http://yd-vl.cztv.com/channels/lantian/channel006/720p.m3u8/{},{}?a=1000".format(dt2stamp(start_time),dt2stamp(end_time))
# channel06 is another choice when channel006 is broken
# 06 is grabbed from http://tv.cztv.com/live1
# 006 is from http://www.cztv.com/live/ the latter one is in a more old-fasion style
videoUrl = "http://yd-vl.cztv.com/channels/lantian/channel06/720p.m3u8/{},{}?a=1000".format(dt2stamp(start_time),dt2stamp(end_time))
videoDownloader(videoUrl, video_name+'.ts')

# sys.exit("Only for downloading")

# ads remover
from commercials_remover import *

qiantang_template = cv2.imread('img/qiantanglaoniangjiu_logo.png',0)
# further cropping
qiantang_template = qiantang_template[25:80 , 666:717]
qiantang_predator = LogoPredator(qiantang_template, 0.7, [10,90,250,900])

huiren_template = cv2.imread('img/huiren_logo_smallist.png',0)
huiren_predator = LogoPredator(huiren_template, 0.7, [92,165,264,356])

# [30,77,660,730] for searching into full logo
# frame_list = get_isads_list(video_name, template, [30,77,660,730], 0.6)
# [30,52,665,720] for only two words "qiantang", 0.6 will be all the wrong matches
# frame_list = get_isads_list(video_name, qiantang_predator, huiren_predator)
frame_list = get_isads_list(video_name, qiantang_predator)


# trim begining
totoal_frames_2_check = len(frame_list)/10
pbar = tqdm(total=totoal_frames_2_check)
template_begin = cv2.imread('img/begin_logo.png', 0)
template_begin = template_begin[170:520,420:800]
begin_predator = LogoPredator(template_begin, 0.7, [140,550,390,830])
cap = cv2.VideoCapture(video_name+".ts")
current_cap_cursor = cap.get(cv2.CAP_PROP_POS_FRAMES)
success, bgr_image = cap.read()
while success and not begin_predator.is_ads(bgr_image):
    pbar.update(1)
    success, bgr_image = cap.read()
    current_cap_cursor = cap.get(cv2.CAP_PROP_POS_FRAMES)
    # only reverse check last 1/10 part
    if current_cap_cursor > totoal_frames_2_check:
        current_cap_cursor = 0
        print("not found!")
        break
pbar.update(totoal_frames_2_check - pbar.n)
pbar.close()
print('the begin is at frame {}'.format(current_cap_cursor))
# begining frames label as priority of 2, to prevent from denoised in case it is a small segment
# the logo lasting about 30 frames
frame_list = len(frame_list[:int(current_cap_cursor+50)])*[2,] + frame_list[int(current_cap_cursor+50):]


# trim ending
totoal_frames_2_check = len(frame_list)/10
pbar = tqdm(total=totoal_frames_2_check)
template_end = cv2.imread('img/end_logo.png', 0)
template_end = template_end[270:400, 1030:1160]
end_predator = LogoPredator(template_end, 0.7, [260,410,1020,1170]) #, [60,222,555,725]
############# uncomment it if cap is not set before ############
# cap = cv2.VideoCapture(video_name+".ts")
# set to the end at first, don't forget to -1
cap.set(cv2.CAP_PROP_POS_FRAMES, len(frame_list)-1)
success, bgr_image = cap.read()
current_cap_cursor = cap.get(cv2.CAP_PROP_POS_FRAMES)
while success and not end_predator.is_ads(bgr_image):
    cap.set(cv2.CAP_PROP_POS_FRAMES, current_cap_cursor-4)
    pbar.update(4-1)
    success, bgr_image = cap.read()
    current_cap_cursor = cap.get(cv2.CAP_PROP_POS_FRAMES)
    print(current_cap_cursor)
    if current_cap_cursor < len(frame_list)-totoal_frames_2_check:
        current_cap_cursor = 0
        print("not found!")
        break
pbar.update(len(frame_list) - pbar.n)
pbar.close()
print('the end is at frame {}'.format(current_cap_cursor))
# the ending frames label as priority of 2, to prevent from denoised in case it is a small segment
frame_list = frame_list[:int(current_cap_cursor-1)] + len(frame_list[int(current_cap_cursor-1):])*[2,]

cap.release()

import pickle
with open(video_name+".picklefile", "wb") as f:
    pickle.dump(frame_list, f)

frame_groups = extract_content_frames(lag_correction(smooth_and_compress2(frame_list)))
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
