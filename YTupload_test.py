# encoding: UTF-8
import commands, os, sys

def cur_file_dir():
     #获取脚本路径
     path = sys.path[0]
     #判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
     if os.path.isdir(path):
         return path
     elif os.path.isfile(path):
         return os.path.dirname(path)

def uploadVideo(ColumnTitle):
    try:
        cmd = 'youtube-upload --title="' + ColumnTitle.encode('utf-8') + '" ' + os.path.join(cur_file_dir(), 'test6.ts' + ' --credentials-file my_credentials.json')
        print(cmd)
        uploadResult = commands.getstatusoutput(cmd)
        print("RESULT: ", uploadResult)
    except Exception as e:
        print e
    if 'error' in uploadResult:
        print 'Error found! Line deleting...'
        # dateDeleter()
        
uploadVideo(u"《钱塘老娘舅》2022年2月6日")