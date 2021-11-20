#!/bin/bash
sudo apt update -y
sudo apt full-upgrade -y
sudo apt install git -y
sudo apt install docker -y
sudo apt install docker-compose -y
grep "start_x=1" /boot/config.txt
if grep "start_x=1" /boot/config.txt
    then
        sed -i "s/start_x=0/start_x=1/g" /boot/config.txt
fi
git clone https://github.com/nbtippetts/ARC.git
cd ARC/
sudo docker-compose up --build -d
#git clone https://github.com/nbtippetts/wpa_wifi_app.git /var/www/html/
#sudo chmod u+x /var/www/html/wpa_wifi_app/bash/install_arc.sh
#cd /var/www/html/wpa_wifi_app/bash/
#./install_arc.sh
#sudo reboot
