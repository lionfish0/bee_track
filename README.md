# bee_track
Tracking software to run on pi

# Installation

Download the aravis library:

    git clone https://github.com/AravisProject/aravis.git
    
Or donwload earlier version from
http://ftp.gnome.org/pub/GNOME/sources/aravis/0.6/

then if you need the viewer:
sudo apt install libgtk-3-dev libnotify-dev libgstreamer1.0 libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-bad

introspection:
??

other stuff...
sudo apt-get install gnome-common intltool valac libglib2.0-dev gobject-introspection libgirepository1.0-dev libgtk-3-dev libclutter-gtk-1.0-dev libgnome-desktop-3-dev libcanberra-dev libgdata-dev libdbus-glib-1-dev libgstreamer1.0-dev libupower-glib-dev
sudo apt-get install libxml2-dev

cd aravis
./configure --enable-viewer --enable-gst-plugin --enable-introspection=yes
make
make install

check if 
aravis-0.6.4/viewer $ ./arv-viewer 
works

(maybe see https://github.com/sightmachine/SimpleCV/wiki/Aravis-(Basler)-GigE-Camera-Install-Guide)

Download this tool

    pip install git+https://github.com/lionfish0/bee_track.git

In /etc/rc.local add line:

su - pi -c /home/pi/bee_track/startup &

