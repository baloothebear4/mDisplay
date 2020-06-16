#!/bin/bash
#
# mDisplay installation script
#
cd /mnt/SDCARD/mDisplay

# 1. Setup boot scripts:
# sudo cp -av config.txt /boot
sudo cp -av rc.local  /etc/rc.local
sudo cp -av shairport-sync.conf /etc
sudo touch /etc/shairport-metadata
sudo cp -av xinitrc ~/.xinitrc

# 2. Install all required python libraries
sudo apt-get update
sudo pip3 install requests
sudo pip3 install fuzzywuzzy
sudo pip3 install python-Levenshtein
sudo pip3 install musicbrainzngs discogs_client tidalapi
sudo apt-get install python3-mutagen python3-mpd
sudo apt-get install python3-pil.imagetk
sudo apt-get install matchbox-window-manager
sudo apt-get -y install nodm matchbox-window-manager
sudo pip3 install luckydonald-utils
sudo pip3 install psutil configparser validators
#
# # 3. Install the python files in pi/prod
mkdir ~/prod
cp -avr ./ ~/prod
#
# # 4. Setup the auto start service
# sudo cp -av mDisplay.service /etc/systemd/system
# sudo chmod 664 /etc/systemd/system/mDisplay.service
# sudo systemctl daemon-reload
# #systemctl start name.service

# 5. Configure Xserver permissions
sudo -u pi touch ~/.Xauthority
sudo -u pi XAUTHORITY=/home/pi/.Xauthority xauth add ${DISPLAY} . $(sudo xauth list | grep 'unix' | tr -s ' ' | cut -d ' ' -f3)
