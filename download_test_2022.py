from hlsdownloader_dynamic_encrypted import videoDownloader
import time, pytz, calendar
from datetime import datetime, timedelta

# def dt2stamp(dt):
    # timestamp = time.mktime(dt.timetuple())
    # return str(int(float(timestamp)*1000))
    
def dt2stamp(dt):
    hours_added = timedelta(hours = 8)
    # my given datetime is in beijing time
    dt -= hours_added
    timestamp = calendar.timegm(dt.timetuple())
    return str(int(float(timestamp)*1000))

# videoUrl = "http://yd-vl.cztv.com/channels/lantian/channel006/720p.m3u8/1643974320000,1643976600000?a=1000"

start_time = datetime(2022, 2, 6, 19, 32, 0, 0)
end_time = datetime(2022, 2, 6, 20, 10, 0, 0)

videoUrl = "http://yd-vl.cztv.com/channels/lantian/channel006/720p.m3u8/{},{}?a=1000".format(dt2stamp(start_time),dt2stamp(end_time))
videoDownloader(videoUrl, 'test6.ts')
print videoUrl

