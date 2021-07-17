import threading
import os
import datetime
import glob
from zipfile import *

class File_Manager():
    def __init__(self,message_queue):
        self.message_queue = message_queue
        
    def compress_photos(self):
        zipfilename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".zip"
        files = glob.glob('*.np')
        with ZipFile(zipfilename, "w", ZIP_DEFLATED) as zip_archive:
            for i,file in enumerate(files):
                self.message_queue.put("Compressing files (%d of %d)" % (i,len(files)))
                self.message_queue.put("<a href='%s'>download</a>" % zipfilename)
                print("Compressing %s" % file)
                zip_archive.write(file)
                #os.remove(file)
