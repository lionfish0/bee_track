# bee_track
Tracking software to run on pi

# Installation

Download the aravis library:

    cd ~ git clone https://github.com/AravisProject/aravis.git

Download this tool

    pip install git+https://github.com/lionfish0/bee_track.git

In /etc/rc.local add line:

su - pi -c /home/pi/bee_track/startup &

