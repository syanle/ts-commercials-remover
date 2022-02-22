from __future__ import division
import cv2, os
import numpy as np
from tqdm import tqdm

template = cv2.imread('qiantanglaoniangjiu_logo_smallist.png',0)
w, h = template.shape[::-1]

def is_ads(img):
    img_rgb = img
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
    # 0.9 will fail if running words blocked
    threshold = 0.8
    loc = np.where( res >= threshold)

    for pt in zip(*loc[::-1]):
        cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0,255,255), 2)

    _is_ads = bool(loc[0].size and loc[1].size)

    return _is_ads

duration = 0
frame_count_read = 0
def get_isads_list(ts_name):
    # read into
    video_capture = cv2.VideoCapture(ts_name+".ts") 

    frame_count = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = video_capture.get(5)
    global duration
    duration = frame_count/fps

    size = (int(video_capture.get(3)), int(video_capture.get(4)))
    frame_index = 0
    flag = 0
    delay = 90
    iscontinue = False
    success, bgr_image = video_capture.read()

    frame_list = []
    # len(frame_list) != frame_count, why?
    pbar = tqdm(total=frame_count)

    while success:  # read frames
        frame_index += 1
        frame_list.append(int(is_ads(bgr_image)))
        success, bgr_image = video_capture.read()
        pbar.update(1)
    pbar.close()
    video_capture.release()
    
    global frame_count_read
    frame_count_read = len(frame_list)
    
    return frame_list
    
from itertools import groupby
def smooth_and_compress(frame_list):
    groups = [(k, sum(1 for i in g)) for k,g in groupby(frame_list)]
    # to find outliers
    for index, group in enumerate(groups):
        # no more than 5 recognization failed consecutive frames in a group (sliding window)
        if group[1] < 30:
            groups[index] = (int(not groups[index][0]), groups[index][1])
    # compress to list of sets
    compressed_groups = []
    for group in groups:
        if len(compressed_groups) == 0:
            compressed_groups.append(group)
            last_group = group
        elif group[0] == last_group[0]:
            compressed_groups[-1] = (compressed_groups[-1][0], compressed_groups[-1][1] + group[1])
            last_group = compressed_groups[-1]
        else:
            compressed_groups.append(group)
            last_group = group
    return compressed_groups
    
def uncompressed_groups(compressed_groups):
    # uncompress to list of list
    list_of_modified_list = [[i[0] for j in range(i[1])] for i in compressed_groups]
    # flat the list of list
    flatted_list = sum(list_of_modified_list, [])
    return flatted_list
    
def extract_content_frames(compressed_groups):
    content_fragments = []
    frame_addup = 0
    for group in compressed_groups:
        if len(content_fragments) == 0:
            if group[0] == 1:
                continue
            elif group[0] == 0:
                content_fragments.append((0, group[1]))
        elif group[0] == 0:
            content_fragments.append((frame_addup+1, frame_addup+group[1]))
        frame_addup += group[1]
    return content_fragments
    
# maybe it will cat at keyframe
# TODO: check if it's meaningful
def round_partial(value, resolution):
    return round (value / resolution) * resolution    
    
def ffmpeg_command_single(ts_name, frame_groups):
    temp_list = []
    for index, frame_group in enumerate(frame_groups):
        time = [round_partial(i/frame_count_read*duration, 0.02) for i in frame_group]
        # https://superuser.com/questions/361329/how-can-i-get-the-length-of-a-video-file-from-the-console
        # have to choose -t duration
        command = "ffmpeg -hide_banner -ss '{:.2f}' -i '{}.ts' -t '{:.2f}' -avoid_negative_ts make_zero -c copy -map '0:0' -map '0:1' -map_metadata 0 -movflags '+faststart' -ignore_unknown -f mpegts -y '{}-seg{:02d}.ts'".format(time[0],ts_name,time[1]-time[0],ts_name,index)
        os.system(command)
        temp_list.append("{}-seg{:02d}.ts".format(ts_name, index))
    # https://stackoverflow.com/questions/47853134/os-system-unable-to-call-file-with-left-parenthesis-in-filename
    # merge_command = "ffmpeg -hide_banner -f concat -safe 0 -protocol_whitelist 'file,pipe' -i <(find . -type f -name '*-seg*ts*' -printf \"file '$PWD/%p'\\n\" | sort) -c copy -map 0 -movflags '+faststart' -ignore_unknown -f mpegts -y '{}-merged.ts'".format(ts_name)
    merge_command = "find . -type f -name '*-seg*ts*' -printf \"file '$PWD/%p'\n\" | sort | ffmpeg -hide_banner -f concat -safe 0 -protocol_whitelist 'file,pipe' -i - -c copy -map 0 -movflags '+faststart' -ignore_unknown -f mpegts -y '{}-merged.ts'".format(ts_name)
    os.system(merge_command)
    os.system("rm *-seg*ts*")
