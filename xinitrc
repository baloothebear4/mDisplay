#!/bin/bash
#
# moOde audio player (C) 2014 Tim Curtis
# http://moodeaudio.org
#
# This Program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This Program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# 2019-10-02 TC moOde 6.3.0
#
#

# Turn on display power management
xset +dpms
xhost +
# Screensaver timeout in secs or 'off' for no timeout
xset s 600

# Capture screen size
SCREENSIZE="$(fbset -s | awk '$1 == "geometry" { print $2","$3 }')"

# Launch chromium browser
# --disk-cache-dir=/dev/null
#chromium-browser --app=http://localhost/ --window-size=$SCREENSIZE --window-position=0,0 --no-first-run --disable-infobars --disable-session-crashed-bubble
matchbox-window-manager -use_cursor no -use_titlebar no  &
export DISPLAY=:0.0
cd ~/prod
#rm mDisplay.log
python3 mDisplay.py > mDisplay.log 2>&1
