from wpa_supplicant.core import WpaSupplicantDriver
from twisted.internet.selectreactor import SelectReactor
import threading
import time
import errno
import sys
import types
import netifaces
import dbus

class PythonWifiScanner:

    wifiAccessPoints = []

    def __init__(self,reactor):
        self._reactor = reactor
        threading.Thread(target=self._reactor.run, kwargs={'installSignalHandlers': 0}).start()
        time.sleep(0.2)  # let reactor start
        self.driver = WpaSupplicantDriver(reactor)
        self.supplicant = self.driver.connect()

        # get network interfaces

        self.net_iface = netifaces.interfaces()

    def get_configured_networks(self,interfaceNumber):
        return self.supplicant.get_interface(self.net_iface[interfaceNumber].decode()).get_networks()

    def get_single_wpa_interface(self,interfaceNumber):
        return self.supplicant.get_interface(self.net_iface[interfaceNumber].decode())

    def get_interfaces(self):
        return self.net_iface

    def select_network(self,network_path,interfaceNumber):
        return self.supplicant.get_interface(self.net_iface[interfaceNumber].decode()).select_network(network_path)

    def add_network(self,network_cfg,interfaceNumber):
        return self.supplicant.get_interface(self.net_iface[interfaceNumber].decode()).add_network(network_cfg)

    def scan_interface_for_networks(self,interfaceNumber):
        # Get interface and scan the network
        interface = self.supplicant.get_interface(self.net_iface[interfaceNumber].decode())
        wifiNetworks = interface.scan(block=True)
        self.wifiAccessPoints = []
        for singleWifi in wifiNetworks:
            self.wifiAccessPoints.append(singleWifi.get_ssid())
        return wifiNetworks

# Start a simple Twisted SelectReactor

sample_network_cfg  = {}
sample_network_cfg['psk'] = "EnterYourKeyHere"
sample_network_cfg['ssid'] = "EnterYourWifiHere"
sample_network_cfg['key_mgmt'] = "WPA-PSK"
reactor = SelectReactor()
dave=PythonWifiScanner(reactor)
value = None
bus = dbus.SystemBus()


print("Interface:" + dave.get_interfaces()[3])

# scan for available networks

for singleWifi in dave.scan_interface_for_networks(3):
    print("Wifi SSID:" + singleWifi.get_ssid())
    print("Wifi Network Type:" + singleWifi.get_network_type())

# Add network configuration to wpa_supplicant

configpath = dave.add_network(sample_network_cfg,3)

# Attach and Select your network (will need to setip address)
dave.select_network(configpath.get_path(),3)
reactor.stop()