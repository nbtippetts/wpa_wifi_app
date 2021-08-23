# -*- coding: utf-8 -*-
from __future__ import print_function
from builtins import str
from builtins import range
Release="0.1b"
#---------------------
from loggerconfig import LOG_SETTINGS
import logging, logging.config, logging.handlers
import basicSetting

DEBUGMODE=basicSetting.data["DEBUGMODE"]
PUBLICMODE=basicSetting.data["PUBLICMODE"]

if DEBUGMODE:
	# below line is required for the loggin of the apscheduler, this might not be needed in the puthon 3.x
	logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)s %(levelname)s %(message)s',
						filename='logfiles/apscheduler_hydrosystem.log',
						filemode='w')


# dedicated logging for the standard operation

logging.config.dictConfig(LOG_SETTINGS)
logger = logging.getLogger('hydrosys4')
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
import selectedplanmod
import networkmod
import networkdbmod
import sysconfigfilemod


# ///////////////// -- GLOBAL VARIABLES AND INIZIALIZATION --- //////////////////////////////////////////
application = Flask(__name__)
application.config.from_object('flasksettings') #read the configuration variables from a separate module (.py) file, this file is mandatory for Flask operations
print("-----------------" , basicSetting.data["INTRO"], "--------------------")


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

@application.route('/network/', methods=['GET', 'POST'])
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
	#print " localwifisystem = ", localwifisystem , " connectedssid ", connectedssid
	message=networkmod.networkdbmod.getstoredmessage()

	return render_template('network.html',filenamelist=filenamelist, connectedssid=connectedssid,localwifisystem=localwifisystem, ipext=ipext, iplocallist=iplocallist , iplocal=iplocal, iplocalwifi=iplocalwifi , ipport=ipport , hostname=hostname, message=message)



@application.route('/wificonfig/', methods=['GET', 'POST'])
def wificonfig():
	if not session.get('logged_in'):
		return render_template('login.html',error=None, change=False)
	print("method " , request.method)
	if request.method == 'GET':
		ssid = request.args.get('ssid')
		print(" argument = ", ssid)

	if request.method == 'POST':
		ssid = request.form['ssid']
		if request.form['buttonsub'] == "Save":
			password=request.form['password']
			#networkmod.savewifi(ssid, password)
			networkmod.waitandsavewifiandconnect(7,ssid,password)
			#redirect to login
			session.pop('logged_in', None)
			return redirect(url_for('login', message="Please wait until the WiFi disconnect and reconnect"))

		elif request.form['buttonsub'] == "Forget":
			print("forget")
			networkmod.waitandremovewifi(7,ssid)
			print("remove network ", ssid)
			print("Try to connect AP")
			networkmod.waitandconnect_AP(9)
			session.pop('logged_in', None)
			return redirect(url_for('login', message="Please wait until the WiFi disconnect and reconnect"))

		else:
			print("cancel")
			return redirect(url_for('network'))

	return render_template('wificonfig.html', ssid=ssid)


@application.route('/echowifi/', methods=['GET'])
def echowifi():
	if not session.get('logged_in'):
		ret_data = {"answer":"Login needed"}
		return jsonify(ret_data)
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

@application.route('/networksetting/', methods=['GET', 'POST'])
def networksetting():
	if not session.get('logged_in'):
		return render_template('login.html',error=None, change=False)
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
				networkdbmod.changesavesetting('LocalIPaddress',IPADDRESS)
				networkdbmod.changesavesetting('LocalAPSSID',AP_SSID)
				networkdbmod.changesavesetting('APtime',AP_TIME)
				networkdbmod.changesavesetting('WIFIENDIS',WIFIENDIS)

				# save and change values in the HOSTAPD config file
				sysconfigfilemod.hostapdsavechangerow("ssid",AP_SSID)
				if AP_PASSWORD!=Fake_password:
					# change password in the HOSTAPD config file
					sysconfigfilemod.hostapdsavechangerow("wpa_passphrase",AP_PASSWORD)
					print("password changed")
				else:
					AP_PASSWORD=""

				if IPADDRESSold!=IPADDRESS:
					# save changes in DHCPCD confign file
					sysconfigfilemod.modifydhcpcdconfigfile(IPADDRESSold, IPADDRESS)

					# save changes in DNSMASQ confign file
					sysconfigfilemod.modifydnsmasqconfigfile(IPADDRESSold, IPADDRESS)

				if HOSTNAME!=HOSTNAMEold:
					networkmod.setnewhostname(HOSTNAME)


				# proceed with changes
				networkmod.applyparameterschange(AP_SSID, AP_PASSWORD, IPADDRESS)
				networkmod.WAITTOCONNECT=AP_TIME
				networkmod.WIFIENDIS=WIFIENDIS

				# Change hostapd file first row with HERE
				data=[]
				networkdbmod.readdata(data)
				sysconfigfilemod.hostapdsavechangerow_spec(data)

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



	return render_template('networksetting.html', IPADDRESS=IPADDRESS, AP_SSID=AP_SSID, AP_PASSWORD=AP_PASSWORD, AP_TIME=AP_TIME , HOSTNAME=HOSTNAME, WIFIENDIS=WIFIENDIS)


if __name__ == '__main__':


	# start web server--------------- -------------------------
	print("start web server")
	global PUBLICPORT
	if PUBLICMODE:
		application.run(debug=DEBUGMODE,use_reloader=False,host= '0.0.0.0',port=networkmod.LOCALPORT)
		#application.run(host='0.0.0.0', debug=True, port=12345, use_reloader=True)
	else:
		application.run(debug=DEBUGMODE,use_reloader=False,port=80)

	print("close")
