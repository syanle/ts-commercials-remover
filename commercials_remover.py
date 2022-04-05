from __future__ import division
import cv2, os, math
import numpy as np
from tqdm import tqdm
from itertools import groupby


# w, h = template.shape[::-1]

def is_ads(img, template, threshold):
    img_rgb = img
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
    # 0.9 will fail if running words blocked
    # threshold = 0.8
    loc = np.where( res >= threshold)

    # plot a box over the matched img
    # for pt in zip(*loc[::-1]):
    #     cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0,255,255), 2)

    _is_ads = bool(loc[0].size and loc[1].size)

    return _is_ads

duration = 0
frame_count_read = 0
# PREFERED_STEP should set to 0, if want to read frame by frame
def get_isads_list(ts_name, template, roi=False, threshold=0.8, PREFERED_STEP=200-1):
    # read into
    video_capture = cv2.VideoCapture(ts_name+".ts") 

    frame_count = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = video_capture.get(5)
    global duration
    duration = frame_count/fps

    size = (int(video_capture.get(3)), int(video_capture.get(4)))

    success, bgr_image = video_capture.read()
    if roi:
        # bgr_image[y:y+h , x:x+w]
        #
        # 0-------------
        # |      [2][3]
        # |   [0]
        # |   [1]
        bgr_image = bgr_image[roi[0]:roi[1] , roi[2]:roi[3]]

    # len(frame_list) != frame_count, why?
    pbar = tqdm(total=frame_count)

    # cap.read() will automatically step to next index
    # that is to say, the STEP means jump-to-jump gaps 
    # iterated frames in one loop = step+read=step+1
    # |last_jump|S|T|E|P|cap.read()|
    # PREFERED_STEP = 200-1 # just regard it as a number, step should be renamed to gap, for a better understanding
    current_step = PREFERED_STEP
    backward_refine_records = None
    last_jump_ads_int = int(is_ads(bgr_image, template, threshold))
    frame_list = [last_jump_ads_int,]
    while success:  # read frames
        current_cap_cursor = video_capture.get(cv2.CAP_PROP_POS_FRAMES)
        # -1 is OK, -10 for safety
        if PREFERED_STEP: # >=0
            # index won't exceed frame_count
            if current_step == PREFERED_STEP and current_cap_cursor+current_step+10 >= frame_count:
                success, bgr_image = video_capture.read()
                ads_int = int(is_ads(bgr_image, template, threshold))
                frame_list.append(ads_int)
                current_step = 1-1 # 0, actually jump frame by frame
                backward_refine_records = None
                last_jump_ads_int = None
            # not near to the end
            else:
                # big jump
                if current_step == PREFERED_STEP:
                    video_capture.set(cv2.CAP_PROP_POS_FRAMES, current_cap_cursor+current_step)
                    # must update after set, otherwise current_cap_cursor in following else condition will be wrong
                    current_cap_cursor = video_capture.get(cv2.CAP_PROP_POS_FRAMES)
                    success, bgr_image = video_capture.read()
                    ads_int = int(is_ads(bgr_image, template, threshold))
                    # same as last big jump
                    if ads_int == last_jump_ads_int:
                        frame_list += [ads_int]*(current_step+1)
                        # pbar.update(current_step+1)
                        last_jump_ads_int = ads_int
                    # return back and re-read
                    else:
                        video_capture.set(cv2.CAP_PROP_POS_FRAMES, current_cap_cursor-current_step)
                        # must update after set
                        current_cap_cursor = video_capture.get(cv2.CAP_PROP_POS_FRAMES)
                        success, bgr_image = video_capture.read()
                        ads_int = int(is_ads(bgr_image, template, threshold))
                        frame_list.append(ads_int)
                        # pbar.update(1)
                        current_step = 0
                        backward_refine_records = []
                        last_jump_ads_int = None # ???
                # frame by frame, but hope to speed up
                else:
                    success, bgr_image = video_capture.read()
                    # to improve
                    if not success:
                        break
                    ads_int = int(is_ads(bgr_image, template, threshold))
                    frame_list.append(ads_int)
                    # pbar.update(1)
                    if backward_refine_records != None:
                        backward_refine_records.append(ads_int)
                        # +30 for safety
                        backward_scope = PREFERED_STEP+30
                        if len(backward_refine_records)>backward_scope and len(set(backward_refine_records[-backward_scope:]))==1:
                            current_step = PREFERED_STEP
                            last_jump_ads_int = ads_int
                            backward_refine_records = None
        # PREFERED_STEP set to 0, always frame by frame
        else:
            success, bgr_image = video_capture.read()
            # to improve
            if not success:
                break
            ads_int = int(is_ads(bgr_image, template, threshold))
            frame_list.append(ads_int)
        pbar.update(video_capture.get(cv2.CAP_PROP_POS_FRAMES) - pbar.n)
        # if not equal, means frame_list appended incorrectly 
        assert len(frame_list) == pbar.n, "frame_list or pbar.n is ahead"
    pbar.close()
    video_capture.release()
    
    global frame_count_read
    frame_count_read = len(frame_list)
    return frame_list

def pooling_denoise(frame_list):
    window = 400
    frame_list_ae_size = int(window/2)
    frame_list_add_empty = [0,]*frame_list_ae_size + frame_list + [0,]*frame_list_ae_size
    frame_list_denosed = []
    for i in range(len(frame_list)):
        window_list = frame_list_add_empty[i:i+frame_list_ae_size]
        window_average = sum(window_list)/len(window_list)
        frame_list_denosed.append(math.ceil(window_average))
    return frame_list_denosed
    
def smooth_and_compress(frame_list):
    groups = [(k, sum(1 for i in g)) for k,g in groupby(frame_list)]
    # to find outliers
    too_small_group = 600
    for index, group in enumerate(groups):
        # no more than 5 consecutive mis-recognized frames in a group (sliding window)
        if group[1] < too_small_group and group[0] == 1:
            groups[index] = (0, groups[index][1])
    # flatten and re-group
    groups = uncompressed_groups(groups)
    groups = [(k, sum(1 for i in g)) for k,g in groupby(groups)]
    # fix #3, must re-check in a new loop
    # invert small groups of 0s in ads
    for index, group in enumerate(groups):
        # no more than 5 consecutive mis-recognized frames in a group (sliding window)
        if group[1] < too_small_group and group[0] == 0:
            groups[index] = (1, groups[index][1])
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

# fix the big scrolling text blocking
# focus on 0 at first
def smooth_and_compress2(frame_list):
    groups = [(k, sum(1 for i in g)) for k,g in groupby(frame_list)]
    # to find big non-ads gaps
    big_enough_group = 600
    for index, group in enumerate(groups):
        # no more than 5 consecutive mis-recognized frames in a group (sliding window)
        if group[1] > big_enough_group and group[0] == 0:
            groups[index] = (-1, groups[index][1])
    # flatten
    groups = uncompressed_groups(groups)
    # if i not -1, than i = i-1
    groups = [0 if i != -1 else i for i in groups]
    # add 1 to all items
    groups = [i+1 for i in groups]
    # group it
    groups = [(k, sum(1 for i in g)) for k,g in groupby(groups)]
    # find too small group of fake 1
    too_small_group = 600
    for index, group in enumerate(groups):
        # no more than 5 consecutive mis-recognized frames in a group (sliding window)
        if group[1] < too_small_group and group[0] == 1:
            groups[index] = (0, groups[index][1])
    # flatten and re-group
    groups = uncompressed_groups(groups)
    compressed_groups = [(k, sum(1 for i in g)) for k,g in groupby(groups)]
    return compressed_groups
    
def uncompressed_groups(compressed_groups):
    # uncompress to list of list
    list_of_modified_list = [[i[0] for j in range(i[1])] for i in compressed_groups]
    # flat the list of list: reshape
    flatted_list = sum(list_of_modified_list, [])
    return flatted_list
    
def extract_content_frames(compressed_groups):
    content_fragments = []
    frame_addup = 0
    for group in compressed_groups:
        if len(content_fragments) == 0:
            if group[0] == 1:
                # add it, before jump out
                frame_addup += group[1]
                continue
            elif group[0] == 0:
                content_fragments.append((frame_addup, frame_addup+group[1]))
        elif group[0] == 0:
            content_fragments.append((frame_addup, frame_addup+group[1]))
        frame_addup += group[1]
    return content_fragments
    
# maybe it will cat at keyframe
# TODO: check if it's meaningful
def round_partial(value, resolution):
    return round (value / resolution) * resolution    
    
def ffmpeg_command_single(ts_name, frame_groups):
    temp_list = []
    for index, frame_group in enumerate(frame_groups):
        # no need to round the cutpoint, since ffmpeg will cut at the nearest keyframe (w/ given paras?
        time = [i/frame_count_read*duration for i in frame_group]
        # https://superuser.com/questions/361329/how-can-i-get-the-length-of-a-video-file-from-the-console
        # have to choose -t duration
        command = "ffmpeg -hide_banner -ss '{:.2f}' -i '{}.ts' -t '{:.2f}' -avoid_negative_ts make_zero -c copy -map '0:0' -map '0:1' -map_metadata 0 -movflags '+faststart' -ignore_unknown -f mpegts -y '{}-seg{:02d}.ts'".format(time[0],ts_name,time[1]-time[0],ts_name,index)
        os.system(command)
        temp_list.append("{}-seg{:02d}.ts".format(ts_name, index))
    os.system("rm {}.ts".format(ts_name))
    # https://stackoverflow.com/questions/47853134/os-system-unable-to-call-file-with-left-parenthesis-in-filename
    # merge_command = "find . -type f -name '{}-seg*ts' -printf \"file '$PWD/%p'\n\" | sort | ffmpeg -hide_banner -f concat -safe 0 -protocol_whitelist 'file,pipe' -i - -c copy -map 0 -movflags '+faststart' -ignore_unknown -f mpegts -y '{}-trimmed.ts'".format(ts_name, ts_name)
    seg_files = ''.join(["file '{}'\n".format(seg) for seg in temp_list])
    merge_command = "printf \"{}\" | ffmpeg -hide_banner -f concat -safe 0 -protocol_whitelist 'file,pipe' -i - -c copy -map 0 -movflags '+faststart' -ignore_unknown -f mpegts -y '{}-trimmed.ts'".format(seg_files, ts_name)
    os.system(merge_command)
    os.system("rm {}-seg*ts".format(ts_name))
