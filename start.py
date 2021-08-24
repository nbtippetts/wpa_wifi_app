#!/usr/bin/python3
Release="0.1b"
#---------------------
from logger_config import LOG_SETTINGS
import logging, logging.config, logging.handlers
import basic_setting

DEBUGMODE=basic_setting.data["DEBUGMODE"]
PUBLICMODE=basic_setting.data["PUBLICMODE"]

if DEBUGMODE:
	# below line is required for the loggin of the apscheduler, this might not be needed in the puthon 3.x
	logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)s %(levelname)s %(message)s',
						filename='logfiles/arc.log',
						filemode='w')


# dedicated logging for the standard operation

logging.config.dictConfig(LOG_SETTINGS)
logger = logging.getLogger('arc')
exc_logger = logging.getLogger('exception')



from flask import Flask, request, session, g, redirect, url_for, abort, \
	 render_template, flash, _app_ctx_stack, jsonify , Response

import requests

from datetime import datetime,date,timedelta
import time
import os
import shutil
import sys
import string
import random
import json
import networkmod
import network_db
import sysconfig_file


# ///////////////// -- GLOBAL VARIABLES AND INIZIALIZATION --- //////////////////////////////////////////
app = Flask(__name__)
app.config.from_object('flask_settings') #read the configuration variables from a separate module (.py) file, this file is mandatory for Flask operations
print("-----------------" , basic_setting.data["INTRO"], "--------------------")


MYPATH=""


# ///////////////// --- END GLOBAL VARIABLES ------



# ///////////////// -- MODULE INIZIALIZATION --- //////////////////////////////////////////


#-- start LOGGING utility--------////////////////////////////////////////////////////////////////////////////////////


#setup log file ---------------------------------------

print("starting new log session", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
logger.info('Start logging -------------------------------------------- %s Version Release: %s' , datetime.now().strftime("%Y-%m-%d %H:%M:%S"),Release)
logger.debug('This is a sample DEBUG message')
logger.info('This is a sample INFO message')
logger.warning('This is a sample WARNING message')
logger.error('This is a sample ERROR message')

isconnecting=False
networkmod.stopNTP()
networkmod.disableNTP()
networkmod.CheckandUnlockWlan()
try:
	print("start networking")
	isconnecting=networkmod.init_network() # this includes also the clock check and scheduler setup
except:
	print("No WiFi available")

@app.route('/')
def home():
	return "<h1>Hello</h1>"

@app.route('/network/', methods=['GET', 'POST'])
def network():
	wifilist=[]
	savedssid=[]
	filenamelist="wifi networks"

	print("visualizzazione menu network:")


	iplocal=networkmod.get_local_ip()
	iplocallist=networkmod.get_local_ip_list()
	ipext=networkmod.get_external_ip()
	iplocalwifi=networkmod.IPADDRESS
	ipport=networkmod.PUBLICPORT
	hostname=networkmod.gethostname()
	connectedssidlist=networkmod.connectedssid()
	if len(connectedssidlist)>0:
		connectedssid=connectedssidlist[0]
	else:
		connectedssid=""


	localwifisystem=networkmod.localwifisystem
	message=networkmod.network_db.getstoredmessage()

	return render_template('network.html',filenamelist=filenamelist, connectedssid=connectedssid,localwifisystem=localwifisystem, ipext=ipext, iplocallist=iplocallist , iplocal=iplocal, iplocalwifi=iplocalwifi , ipport=ipport , hostname=hostname, message=message)



@app.route('/wifi_config/', methods=['GET', 'POST'])
def wifi_config():
	print("method " , request.method)
	if request.method == 'GET':
		ssid = request.args.get('ssid')
		print(" argument = ", ssid)

	if request.method == 'POST':
		ssid = request.form['ssid']
		if request.form['buttonsub'] == "Save":
			password=request.form['password']
			networkmod.waitandsavewifiandconnect(7,ssid,password)
			#redirect to network
			return redirect(url_for('network', message="Please wait until the WiFi disconnect and reconnect"))

		elif request.form['buttonsub'] == "Forget":
			print("forget")
			networkmod.waitandremovewifi(7,ssid)
			print("remove network ", ssid)
			print("Try to connect AP")
			networkmod.waitandconnect_AP(9)
			return redirect(url_for('network', message="Please wait until the WiFi disconnect and reconnect"))

		else:
			print("cancel")
			return redirect(url_for('network'))

	return render_template('wifi_config.html', ssid=ssid)


@app.route('/echo_wifi/', methods=['GET'])
def echo_wifi():
	ret_data={}
	element=request.args['element']
	if element=="all":
		# get wifi list
		wifilist=[]
		wifilist=networkmod.wifilist_ssid(2)
		connectedssidlist=networkmod.connectedssid()
		if len(connectedssidlist)>0:
			connectedssid=connectedssidlist[0]
		else:
			connectedssid=""

		savedssid=networkmod.savedwifilist_ssid()
		#print "Saved SSIDs ", savedssid

		for ssid in wifilist:
			connected="0"
			if ssid==connectedssid:
				connected="1"
			idstatus="Unknown"
			if ssid in savedssid:
				idstatus="Saved"

			ret_data[ssid]=[idstatus , connected]

	#print "Wifi Data " , ret_data
	return jsonify(ret_data)

@app.route('/network_setting/', methods=['GET', 'POST'])
def network_setting():
	error = None

	Fake_password="AP-password"

	if request.method == 'POST':
		print(" here we are at network setting")
		reqtype = request.form['button']
		if reqtype=="save":
			print("saving network advanced setting")
			gotADDRESS=request.form['IPADDRESS']
			AP_SSID=request.form['AP_SSID']
			AP_PASSWORD=request.form['AP_PASSWORD']
			AP_TIME=request.form['AP_TIME']
			WIFIENDIS=request.form['WIFIENDIS']
			HOSTNAME=request.form['HOSTNAME']



			# Check
			isok1 , IPADDRESS = networkmod.IPv4fromString(gotADDRESS)
			isok2=False
			isok3=False
			if len(AP_PASSWORD)>7:
				isok2=True
			if len(AP_SSID)>3:
				isok3=True





			if isok1 and isok2 and isok3:

				# previous paramenters
				IPADDRESSold=networkmod.IPADDRESS
				AP_SSIDold=networkmod.localwifisystem
				AP_TIMEold=str(networkmod.WAITTOCONNECT)
				HOSTNAMEold=networkmod.gethostname()
				WIFIENDISold=networkmod.WIFIENDIS



				print("save in network file in database")
				network_db.changesavesetting('LocalIPaddress',IPADDRESS)
				network_db.changesavesetting('LocalAPSSID',AP_SSID)
				network_db.changesavesetting('APtime',AP_TIME)
				network_db.changesavesetting('WIFIENDIS',WIFIENDIS)

				# save and change values in the HOSTAPD config file
				sysconfig_file.hostapdsavechangerow("ssid",AP_SSID)
				if AP_PASSWORD!=Fake_password:
					# change password in the HOSTAPD config file
					sysconfig_file.hostapdsavechangerow("wpa_passphrase",AP_PASSWORD)
					print("password changed")
				else:
					AP_PASSWORD=""

				if IPADDRESSold!=IPADDRESS:
					# save changes in DHCPCD confign file
					sysconfig_file.modifydhcpcdconfigfile(IPADDRESSold, IPADDRESS)

					# save changes in DNSMASQ confign file
					sysconfig_file.modifydnsmasqconfigfile(IPADDRESSold, IPADDRESS)

				if HOSTNAME!=HOSTNAMEold:
					networkmod.setnewhostname(HOSTNAME)


				# proceed with changes
				networkmod.applyparameterschange(AP_SSID, AP_PASSWORD, IPADDRESS)
				networkmod.WAITTOCONNECT=AP_TIME
				networkmod.WIFIENDIS=WIFIENDIS

				# Change hostapd file first row with HERE
				data=[]
				network_db.readdata(data)
				sysconfig_file.hostapdsavechangerow_spec(data)

				if WIFIENDISold!=WIFIENDIS:
					if WIFIENDIS=="Disabled":
						networkmod.Disable_WiFi()
					else:
						networkmod.connect_network()

				flash('Network setting Saved')
				return redirect(url_for('network'))
			else:
				if not isok1:
					flash('please input valid IP address','danger')
				if not isok2:
					flash('please input password longer than 7 characters','danger')
				if not isok3:
					flash('please input SSID longer than 3 characters','danger')
		elif reqtype=="cancel":
			return redirect(url_for('network'))


	HOSTNAME=networkmod.gethostname()
	iplocal=networkmod.get_local_ip()
	IPADDRESS=networkmod.IPADDRESS
	PORT=networkmod.PUBLICPORT
	AP_SSID=networkmod.localwifisystem
	AP_TIME=str(networkmod.WAITTOCONNECT)
	WIFIENDIS=networkmod.WIFIENDIS
	connectedssidlist=networkmod.connectedssid()
	if len(connectedssidlist)>0:
		connectedssid=connectedssidlist[0]
	else:
		connectedssid=""
	AP_PASSWORD=Fake_password



	return render_template('network_setting.html', IPADDRESS=IPADDRESS, AP_SSID=AP_SSID, AP_PASSWORD=AP_PASSWORD, AP_TIME=AP_TIME , HOSTNAME=HOSTNAME, WIFIENDIS=WIFIENDIS)


if __name__ == '__main__':


	# start web server--------------- -------------------------
	print("start web server")
	app.run(debug=DEBUGMODE,use_reloader=False,port=80)

	print("close")
