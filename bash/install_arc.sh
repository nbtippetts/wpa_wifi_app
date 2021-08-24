#!/bin/bash

# ENV VARS
IP="192.168.1.172"
PORT="9818"
WiFiAPname="ARC_WIFI"
WiFiAPpsw="arc_secret"
MQTTsupport="y"
ChangeHostName="y"
NewHostName="the-arc"
doreboot="y"

#Debug enable next 3 lines
exec 5> install.txt
BASH_XTRACEFD="5"
set -x
# ------ end debug


function killpython()
{

sudo killall python3

}


function system_update_light()
{

# ---- system_update

sudo apt-get -y update

}

function system_update()
{

# ---- remove unnecessary packages

sudo apt-get remove --purge libreoffice-*
sudo apt-get remove --purge wolfram-engine


# ---- system_update

sudo apt-get -y update
sudo apt-get -y upgrade

}

function system_update_UI()
{

while true; do
    read -p "Do you wish to update the Raspbian system (y/n)?" yn
    case $yn in
        [Yy]* ) system_update; break;;
        [Nn]* ) break;;
        * ) echo "Please answer y or n.";;
    esac
done

}

function install_dependencies()
{


#--- start installing dependencies

sudo apt-get -y install python3-dev || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}
sudo apt -y install python3-pip || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}
sudo pip3 install flask || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}
sudo pip3 install apscheduler || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}
sudo pip3 install pyserial || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}
sudo apt-get install python3-future

#(for the webcam support)
sudo apt-get -y install fswebcam || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}

#(for the image thumbnail support)
sudo apt-get -y install libjpeg-dev || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}
sudo apt install libopenjp2-7
sudo pip3 install pillow || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}

#(for external IP address, using DNS)
sudo apt-get -y install dnsutils || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}

#(encryption)
sudo pip3 install pbkdf2 || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}

#(web server)
sudo pip3 install tornado || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}

#(GPIO)
sudo pip3 install RPi.GPIO
}

function enable_I2C()
{

# --- Enable I2C and Spi :
# /boot/config.txt

sed -i 's/\(^.*#dtparam=i2c_arm=on.*$\)/dtparam=i2c_arm=on/' /boot/config.txt
sed -i 's/\(^.*#dtparam=spi=on.*$\)/dtparam=spi=on/' /boot/config.txt
sed -i 's/\(^.*#dtparam=i2s=on.*$\)/dtparam=i2s=on/' /boot/config.txt

# --- Add modules:
# /etc/modules
aconf="/etc/modules"

sed -i '/i2c-bcm2708/d' $aconf
sed -i -e "\$ai2c-bcm2708" $aconf

sed -i '/i2c-dev/d' $aconf
sed -i -e "\$ai2c-dev" $aconf

sed -i '/i2c-bcm2835/d' $aconf
sed -i -e "\$ai2c-bcm2835" $aconf

sed -i '/rtc-ds1307/d' $aconf
sed -i -e "\$artc-ds1307" $aconf

sed -i '/bcm2835-v4l2/d' $aconf
sed -i -e "\$abcm2835-v4l2" $aconf


# --- install I2C tools
sudo apt-get -y install git build-essential python3-dev python3-smbus || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}
sudo apt-get -y install -y i2c-tools  || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}

}


# --- enable raspicam

############# MISSING ##############

function modify_RClocal()
{

# --- Real Time Clock (RTC)
# /etc/rc.local

autostart="yes"
# copy the below lines between # START and #END to rc.local
tmpfile=$(mktemp)
sudo sed '/#START/,/#END/d' /etc/rc.local > "$tmpfile" && sudo mv "$tmpfile" /etc/rc.local
# Remove to growing plank lines.
sudo awk '!NF {if (++n <= 1) print; next}; {n=0;print}' /etc/rc.local > "$tmpfile" && sudo mv "$tmpfile" /etc/rc.local
if [ "$autostart" == "yes" ]; then
   if ! grep -Fq '#START ARC SECTION' /etc/rc.local; then
      sudo sed -i '/exit 0/d' /etc/rc.local
      sudo bash -c "cat >> /etc/rc.local" << EOF
#START ARC SECTION
# iptables
sudo iptables-restore < /home/pi/iptables.rules

# clock
echo "ARC-set HW clock ****************************************"
echo ds3231 0x68 > /sys/class/i2c-adapter/i2c-1/new_device || true
hwclock -s || true

echo "ARC-start-web system ****************************************"
cd /var/www/html/wpa_wifi_app/
export FLASK_APP=start
flask run

#END ARC SECTION

exit 0
EOF
   else
      tmpfile=$(mktemp)
      sudo sed '/#START/,/#END/d' /etc/rc.local > "$tmpfile" && sudo mv "$tmpfile" /etc/rc.local
      # Remove to growing plank lines.
      sudo awk '!NF {if (++n <= 1) print; next}; {n=0;print}' /etc/rc.local > "$tmpfile" && sudo mv "$tmpfile" /etc/rc.local
   fi

fi

sudo chown root:root /etc/rc.local
sudo chmod 755 /etc/rc.local
# end modification to RC.local

}


### -- WIFI setup --- STANDARD

function valid_ip()
{
    local  ip=$1
    local  stat=1

    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        OIFS=$IFS
        IFS='.'
        ip=($ip)
        IFS=$OIFS
        [[ ${ip[0]} -le 255 && ${ip[1]} -le 255 \
            && ${ip[2]} -le 255 && ${ip[3]} -le 255 ]]
        stat=$?
    fi
    return $stat
}

# input_UI ()
# {

# echo "Hello, following initial setting is requested:"

# # IP part input
# while ! valid_ip $IP; do
# 	read -p "Local IP address (range 192.168.1.100-192.168.1.200), to confirm press [ENTER] or modify: " -e -i 192.168.1.172 IP
# 	if valid_ip $IP; then stat='good';
# 	else stat='bad'; echo "WRONG FORMAT, please enter a valid value for IP address"
# 	fi

# done
# 	echo "Confirmed IP address: "$IP

# PORT=""
# while [[ ! $PORT =~ ^[0-9]+$ ]]; do
# read -p "Local PORT, to confirm press [ENTER] or modify: " -e -i 9818 PORT
# 	if [[ ! $PORT =~ ^[0-9]+$ ]];
# 	then echo "WRONG FORMAT, please enter a valid value for PORT";
# 	fi
# done
# 	echo "Confirmed PORT: "$PORT

# # Local WiFi AP name and password setting

# read -p "System WiFi AP name, to confirm press [ENTER] or modify: " -e -i ARC_WIFI WiFiAPname
# echo "Confirmed Name: "$WiFiAPname

# read -p "System WiFi AP password, to confirm press [ENTER] or modify: " -e -i arc_secret WiFiAPpsw
# echo "Confirmed Password: "$WiFiAPpsw

# read -p "Do you want to change hostname? (y,n): " -e -i y ChangeHostName
# echo "Confirmed Answer: "$ChangeHostName

# if [ "$ChangeHostName" == "y" ]; then
# 	read -p "System Hostname, to confirm press [ENTER] or modify: " -e -i arc-9818 NewHostName
# 	echo "Confirmed Hostname: "$NewHostName
# fi

# read -p "Do you want to install MQTT support? (y,n): " -e -i y MQTTsupport
# echo "Confirmed Answer: "$MQTTsupport

# }


install_MQTTsupport ()
{

# --- change system hostname
if [ "$MQTTsupport" == "y" ]; then

	sudo apt-get -y install mosquitto || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}
	sudo pip3 install paho-mqtt

fi

}


apply_newhostname ()
{

# --- change system hostname
if [ "$ChangeHostName" == "y" ]; then
	sudo hostnamectl set-hostname $NewHostName # change the name in /etc/hostname

	aconf="/etc/hosts"
	# Update hostapd main config file
	sudo sed -i "s/127.0.1.1.*/127.0.1.1	"$NewHostName"/" $aconf

fi

}


ask_reboot ()
{


# read -p "Do you want to reboot the system? (y,n): " -e -i y doreboot
# echo "Confirmed Answer: "$doreboot

if [ "$doreboot" == "y" ]; then
	sudo reboot
fi

}



install_arc ()
{
# --- INSTALL ARC software
sudo apt-get -y install git || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}


# check if file exist in local folder
#aconf="/home/pi/env/autonom"
#if [ -d $aconf ]; then  # if the directory exist
#	cd /home/pi
#else
	cd /home/pi
	sudo killall python3
	sudo rm -r env
	mkdir env
	cd env
	#sudo rm -r autonom
	git clone https://github.com/nbtippetts/ARC.git
	cd ..
	cd ..

#fi

}






fn_hostapd ()
{

sudo apt-get -y install hostapd || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}

# unmask the service
sudo systemctl unmask hostapd.service

# create hostapd.conf file
aconf="/etc/hostapd/hostapd.conf"
if [ -f $aconf ]; then
   cp $aconf $aconf.1
   sudo rm $aconf
   echo "remove file"
fi


sudo bash -c "cat >> $aconf" << EOF
# HERE-> {"name": "IPsetting", "LocalIPaddress": "$IP", "LocalPORT": "$PORT", "LocalAPSSID" : "$WiFiAPname"}
ieee80211n=1
interface=wlan0
ssid=$WiFiAPname
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$WiFiAPpsw
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF


aconf="/etc/init.d/hostapd"
# Update hostapd main config file
sudo sed -i "s/\(^.*DAEMON_CONF=.*$\)/DAEMON_CONF=\/etc\/hostapd\/hostapd.conf/" $aconf

aconf="/etc/default/hostapd"
# Update hostapd main config file
sudo sed -i "s/\(^.*DAEMON_CONF=.*$\)/DAEMON_CONF=\/etc\/hostapd\/hostapd.conf/" $aconf

sudo systemctl enable hostapd.service

}


fn_dnsmasq ()
{

sudo apt-get -y install dnsmasq || { echo "ERROR --------------------------Installation failed ----------------" && exit ;}


# edit /etc/dnsmasq.conf file
aconf="/etc/dnsmasq.conf"

# delete rows between #START and #END
sed -i '/^#START ARC SECTION/,/^#END ARC SECTION/{/^#START ARC SECTION/!{/^#END ARC SECTION/!d}}' $aconf
sed -i '/#START ARC SECTION/d' $aconf
sed -i '/#END ARC SECTION/d' $aconf

# calculation of the range starting from assigned IP address
IFS="." read -a a <<< $IP
IFS="." read -a b <<< 0.0.0.1
IFS="." read -a c <<< 0.0.0.9
IPSTART="$[a[0]].$[a[1]].$[a[2]].$[a[3]+b[3]]"
IPEND="$[a[0]].$[a[1]].$[a[2]].$[a[3]+c[3]]"
if [[ a[3] -gt 244 ]]; then
IPSTART="$[a[0]].$[a[1]].$[a[2]].$[a[3]-c[3]]"
IPEND="$[a[0]].$[a[1]].$[a[2]].$[a[3]-b[3]]"
fi

echo $IPSTART $IPEND



# -----



sudo bash -c "cat >> $aconf" << EOF
#START ARC SECTION
interface=wlan0
dhcp-range=$IPSTART,$IPEND,12h
#no-resolv
#END ARC SECTION
EOF

sudo systemctl enable dnsmasq.service


}


fn_dhcpcd ()
{

# edit /etc/dnsmasq.conf file
aconf="/etc/dhcpcd.conf"

# delete rows between #START and #END
sed -i '/^#START ARC SECTION/,/^#END ARC SECTION/{/^#START ARC SECTION/!{/^#END ARC SECTION/!d}}' $aconf
sed -i '/#START ARC SECTION/d' $aconf
sed -i '/#END ARC SECTION/d' $aconf


sudo bash -c "cat >> $aconf" << EOF
#START ARC SECTION
profile static_wlan0
static ip_address=$IP/24
#static routers=192.168.1.1
#static domain_name_servers=192.169.1.1
# fallback to static profile on wlan0
interface wlan0
fallback static_wlan0
#END ARC SECTION
EOF


}

fn_ifnames ()
{
# this is to preserve the network interfaces names, becasue staring from debian stretch (9) the ifnames have new rules
# edit /etc/dnsmasq.conf file
aconf="/boot/cmdline.txt"

APPEND=' net.ifnames=0'
echo "$(cat $aconf)$APPEND" > $aconf

}

install_nginx ()
{
# this function is used
cd /home/pi

sudo apt-get -y install nginx

# create default file
aconf="/etc/nginx/sites-enabled/default"
if [ -f $aconf ]; then
   cp $aconf /home/pi/$aconf.1
   sudo rm $aconf
   echo "remove file"
fi


sudo bash -c "cat >> $aconf" << EOF
server {
    # for a public HTTP server:
    listen $PORT;
    server_name localhost;
    access_log off;
    error_log off;
    location / {
        proxy_pass http://127.0.0.1:5000;
    }
    location /stream {
        rewrite ^/stream/(.*) /$1 break;
        proxy_pass http://127.0.0.1:5000;
        proxy_buffering off;
    }
    location /favicon.ico {
        alias /home/pi/env/autonom/static/favicon.ico;
    }
}
EOF

sudo service nginx start

cd ..
cd ..

}
edit_defaultnetworkdb ()
{


aconf="/home/pi/env/autonom/database/default/defnetwork.txt "

# if file already exist then no action, otherwise create it
if [ -f $aconf ]; then
   echo "network default file already exist"
   else
   sudo bash -c "cat >> $aconf" << EOF
{"name": "IPsetting", "LocalIPaddress": "192.168.0.172", "LocalPORT": "9818" , "LocalAPSSID" : "ARC_WIFI"}
EOF

fi

}

edit_networkdb ()
{


aconf="/home/pi/env/autonom/database/network.txt "

# if file already exist then delete it
if [ -f $aconf ]; then
   sudo rm $aconf
   echo "remove file"
fi

sudo bash -c "cat >> $aconf" << EOF
{"name": "IPsetting", "LocalIPaddress": "$IP", "LocalPORT": "$PORT", "LocalAPSSID" : "$WiFiAPname"}
EOF


}


iptables_blockports ()
{
sudo iptables -A INPUT -p tcp -s localhost --dport 5020 -j ACCEPT
sudo iptables -A INPUT -p tcp -s localhost --dport 5022 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5020 -j DROP
sudo iptables -A INPUT -p tcp --dport 5022 -j DROP

sudo iptables-save > /home/pi/iptables.rules

}


# --- RUN the functions
killpython
system_update_light
install_dependencies
enable_I2C
modify_RClocal
fn_hostapd
fn_dnsmasq
fn_dhcpcd
fn_ifnames
install_mjpegstr
install_nginx
install_SPIlib
install_MQTTsupport
edit_defaultnetworkdb
iptables_blockports
apply_newhostname
echo "installation is finished!!! "
# ask_reboot
