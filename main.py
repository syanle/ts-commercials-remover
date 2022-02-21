# coding:utf-8
from hlsdownloader_dynamic_encrypted import videoDownloader
import time, calendar
from datetime import datetime, timedelta

    
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

video_name = u"《钱塘老娘舅》"+start_time.strftime("%Y年%m月%d日").decode("utf-8")

videoUrl = "http://yd-vl.cztv.com/channels/lantian/channel006/720p.m3u8/{},{}?a=1000".format(dt2stamp(start_time),dt2stamp(end_time))
videoDownloader(videoUrl, video_name+'.ts')


# ads remover
from commercials_remover import *

frame_list = get_isads_list(video_name)
frame_groups = extract_content_frames(smooth_and_compress(frame_list))
ffmpeg_command_single(video_name, frame_groups)

# YouTube uploader
import commands, os, sys

def cur_file_dir():
     #获取脚本路径
     path = sys.path[0]
     #判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的>文件，则返回的是编译后的文件路径
     if os.path.isdir(path):
         return path
     elif os.path.isfile(path):
         return os.path.dirname(path)

def uploadVideo(ColumnTitle):
    cmd = 'youtube-upload --title="' + ColumnTitle.encode('utf-8') + '" ' + os.path.join(cur_file_dir(), video_name.encode('utf-8') + '.ts' + ' --client-secrets=client_secret_2017_jitoushan.json')
    print cmd
    uploadResult = commands.getstatusoutput(cmd)
    print("RESULT: ", uploadResult)
    if 'error' in uploadResult:
        # dateDeleter()
        print 'Error found! Line deleting...'

# Youtube API aquires audit these days
# uploadVideo(video_name)
