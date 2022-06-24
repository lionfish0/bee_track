#  If you have installed aravis in a non standard location, you may need
#   to make GI_TYPELIB_PATH point to the correct location. For example:
#
#   export GI_TYPELIB_PATH=$GI_TYPELIB_PATH:/opt/bin/lib/girepositry-1.0/
#
#  You may also have to give the path to libaravis.so, using LD_PRELOAD or
#  LD_LIBRARY_PATH.

import sys
import gi
import numpy as np

gi.require_version ('Aravis', '0.8')

from gi.repository import Aravis

Aravis.enable_interface ("Fake")

try:
    if len(sys.argv) > 1:
        camera = Aravis.Camera.new (sys.argv[1])
    else:
        camera = Aravis.Camera.new (None)
except TypeError:
	print ("No camera found")
	exit ()

#camera.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)
#camera.set_region (0,0,128,128)
#camera.set_frame_rate (10)
#camera.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)

aravis_device = camera.get_device();
print("---")
aravis_device.set_string_feature_value("TriggerMode", "On")
aravis_device.set_string_feature_value("TriggerSource", "Software")
aravis_device.set_string_feature_value("LineSelector", "Line2")
aravis_device.set_boolean_feature_value("StrobeEnable", False)
#aravis_device.set_string_feature_value("LineMode", "Strobe")
aravis_device.set_string_feature_value("LineSource", "ExposureStartActive")
print(aravis_device.get_string_feature_value("LineSource"))
print(aravis_device.get_boolean_feature_value("LineStatus"))
aravis_device.set_boolean_feature_value("LineInverter",True)
#aravis_device.set_integer_feature_value("LineMode", 0)
print(aravis_device.get_string_feature_value("LineMode"))

#aravis_device.set_string_feature_value("Trigger, "On")

#arv_device_set_string_feature_value(Device, "TriggerMode", "On");
#arv_device_set_string_feature_value(Device, "TriggerSource", "Line1");
#arv_device_set_string_feature_value(Device, "TriggerActivation", "RisingEdge");
#arv_device_set_string_feature_value(Device, "AcquisitionMode", "Continuous");

camera.set_exposure_time(10000)
payload = camera.get_payload ()

[x,y,width,height] = camera.get_region ()

print ("Camera vendor : %s" %(camera.get_vendor_name ()))
print ("Camera model  : %s" %(camera.get_model_name ()))
print ("ROI           : %dx%d at %d,%d" %(width, height, x, y))
print ("Payload       : %d" %(payload))
print ("Pixel format  : %s" %(camera.get_pixel_format_as_string ()))
camera.set_gain(10)
#camera.set_trigger("Line1")

stream = camera.create_stream (None, None)

for i in range(0,10):
	stream.push_buffer (Aravis.Buffer.new_allocate (payload))

print ("Start acquisition")
camera.start_acquisition ()

print ("Acquisition")

def ascii_draw(mat):
    symbols = np.array([s for s in ' .,:-=+*X#@@'])#[::-1]
    msg = ""
    mat = (11*mat/(np.max(mat)+1)).astype(int)
    mat[mat<0] = 0
    for i in range(0,len(mat),2):
        msg+=''.join(symbols[mat][i])+"\n"
    return msg

while (True):
	camera.software_trigger()
	image = stream.pop_buffer ()
	if image:
		#print(image.get_status())
		raw = np.frombuffer(image.get_data(),dtype=np.uint8).astype(float).reshape(2048,1536) 
                print(ascii_draw(raw[::20,::12]))
		stream.push_buffer (image)

print ("Stop acquisition")

camera.stop_acquisition ()

