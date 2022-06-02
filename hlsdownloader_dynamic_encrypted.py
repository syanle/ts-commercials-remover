#!/usr/bin/python
# coding:utf-8

import m3u8

try:
    from urllib.request import urlopen
    from urllib.error import URLError
    from urllib.parse import urlparse
except ImportError:  # Python 2.x
    from urllib2 import urlopen, URLError
    from urlparse import urlparse

from sys import argv, version_info
import time
from retry_decorator import retry
import socket

from hashlib import md5

PYTHON_MAJOR_VERSION = version_info

deviceid = '315f94910a31a816fdba1fda12e0a7ac'
size_list = []

# liuliang saving
###
# import urllib2
# proxy = urllib2.ProxyHandler({
    # 'http': '127.0.0.1:1081',
    # 'https': '127.0.0.1:1081'
# })
# opener = urllib2.build_opener(proxy)
# urllib2.install_opener(opener)
###

def py_md5(s):
    if PYTHON_MAJOR_VERSION < (3,):
        return md5(s).hexdigest()
    else:
        return md5(s.encode('utf-8')).hexdigest()

def getencrypion(deviceid):
    d = deviceid
    t = str(int(time.time()))
    timefragment = t[-5:]
    k = py_md5(t + d + '7ea5d67d5d703d7d5b981a26eaaa5e3e' + py_md5(timefragment))

    return k

# https://stackoverflow.com/questions/9446387/how-to-retry-urllib2-request-when-fails
@retry(Exception, tries=5, delay=10, backoff=5)
def urlopen_with_retry(link):
    resp = urlopen(link, timeout=30)
    # read it in @retry. If timeout were exceeded, 
    # no error raised since urlopen would return normally without any data in it
    # therefore I have to raise it by resp.read() to ensure when I got null data,
    # I also need to retry
    return (resp, resp.read())

# why to use request? For downloading real-time streaming?
# import requests
# class RequestsClient():
    # def download(self, uri, timeout=None, headers={}, verify_ssl=True):
        # o = requests.get(uri, timeout=timeout, headers=headers)
        # return o.text, o.url

def videoDownloader(fileUrl, filePath):
    ts_file = open(filePath, "wb")

    retrive_seq = -1 
    Err_flag = False

    while not Err_flag :
        encrypted_fileUrl = "{}&d={}&k={}&t={}".format(fileUrl, deviceid, getencrypion(deviceid), str(int(time.time())))
        print(encrypted_fileUrl)
        # m3u8_obj = m3u8.load(encrypted_fileUrl, http_client=RequestsClient())
        m3u8_obj = m3u8.load(encrypted_fileUrl)
        print("encrypted_fileUrl updated")

        new_seg_flag = False
        print(time.strftime('%Y-%m-%d %H:%M:%S ',time.localtime(time.time())) , "#EXT-X-MEDIA-SEQUENCE:", m3u8_obj.media_sequence)
        
        seg_seq = m3u8_obj.media_sequence

        print('len:', len(m3u8_obj.segments))
        
        for seg in  m3u8_obj.segments:
            # seg = #EXTINF:10.000615
            if m3u8.is_url(seg.uri):
                segurl = seg.uri
            else :
                # segurl =  m3u8.model._urijoin( seg.base_uri ,  seg.uri )
                parsed_url = urlparse(seg.base_uri)
                prefix = parsed_url.scheme + '://' + parsed_url.netloc
                segurl =  prefix + seg.uri
        
            if seg_seq > retrive_seq :
                if retrive_seq>=0 and seg_seq!=retrive_seq+1 :
                    print("WARN: SEQ not continue!!!! %d - %d" , retrive_seq , seg_seq)

                retrive_seq = seg_seq        
                new_seg_flag = True
                #print segurl
                
                # check for the integrity of segs
                resp_repeat_size = []
                while True:
                    start_ts = time.time()
                    
                    try:
                        resp_tuple = urlopen_with_retry(segurl)
                        resp = resp_tuple[0]
                    except Exception as e:
                        # exceeds max trying times
                        print(e, "This seg losts permanently, sleeping for 15 min")
                        time.sleep(900)
                        continue
                        
                    try:
                        doc = resp_tuple[1]
                    except Exception as e:
                        print(e)
                    size = len(resp_tuple[1])

                    if resp.getcode()!=200 :
                        print("Error HTTP resp code:" , resp.getcode(), segurl)
                        # check here
                        Err_flag = True
                        break    

                    resp.close()

                    end_ts  = time.time()
                    dur = end_ts-start_ts
                    if dur > 8 :
                        print("Error TOO SLOW!!!!! " ,  dur, size , size*8/dur/1024,  " - ", segurl) 
                    else:
                        print(dur, size , size*8/dur/1024,  " - ", segurl)
                    
                    # a valid mpeg-ts seg is always the times of 188
                    # also add robustness in case the sever side seg was already broken
                    if size % 188 == 0 or (len(resp_repeat_size) > 2 and size == resp_repeat_size[-1] == resp_repeat_size[-2]):
                        break
                    else:
                        resp_repeat_size.append(size)

                ts_file.write(doc)     
            
            time.sleep(dur)
            seg_seq = seg_seq + 1
            
        if m3u8_obj.is_endlist:
            break;
        elif not new_seg_flag :
            time.sleep(20) 
            print("sleep 20s to wait to get next m3u8 list...") 

    ts_file.close()
