#!/usr/bin/python2.7 -3
#-*- coding: utf-8 -*-

#
# (c) Raphael Jacquot 2014
# Licenced under the terms of the GNU GPL v3.0 or later
#

import config
import json
import myOpenLayer1
#import myOpenTempControl
import re

class MyOpenApplication (object) :
    COMMAND                   = 0
    STATUS                    = 1
    MSG_TYPES                 = [ 'Command', 'Status', ]

    SYSTEM__LIGHTING          = 1
    SYSTEM__TEMP_CONTROL      = 4

    LIGHTING__OFF             = 0
    LIGHTING__ON              = 1

    TEMP_CONTROL__REPORT_TEMP = 0

    def __init__ (self) :
        # prepare the app startup
        self.routes = [ { '1' : self.cmd_lighting, },
                        { '4' : self.status_tempcontrol}, ]
        # initializes callbacks
        self.callbacks = None
        # create the system loop
        self.system_loop = myOpenLayer1.MainLoop(myOpenLayer1.system_logger)
        # open the monitor socket to the gateway
        self.monitor_socket = myOpenLayer1.OwnSocket(
                config.host,
                config.port,
                config.password,
                myOpenLayer1.OwnSocket.MONITOR)
        # set the callback to get messages from the layer 1
        self.monitor_socket.set_data_callback(self.data_callback)
        # add the monitor socket to the system loop
        self.system_loop.add_socket(self.monitor_socket)

    def log (self, msg) :
        msg = unicode(msg)
        if self.monitor_socket is not None: 
            self.monitor_socket.log (msg)
        else:
            print (msg)
    
    def run (self) :
        # run the system loop.
        self.system_loop.run()

    def get_number (self, msg) :
        v = '' 
        while True :
            if len(msg) == 0 :
                break
            c = msg[0]
            if c >= '0' and c <= '9' :
                v += c
                msg = msg[1:]
            else :
                break
        return v, msg

    def data_callback (self, msg) :
        msgtype = None
        # analyze the content of messages passed from the layer 1
        m = re.match('^\*(?P<who>\d+)(?P<msg>\*.*)', msg)
        if m is not None :
            msgtype = self.COMMAND
        else :
            m = re.match('^\*#(?P<who>\d+)(?P<msg>\*.*)', msg)
            if m is not None :
                msgtype = self.STATUS
        if msgtype is not None :
            r = self.routes[msgtype]
            who, msg = m.groups()
            if who in r :
                func = r[who]
                if func is not None :
                    func (msg)
                    return
            msg = 'found '+self.MSG_TYPES[msgtype]+' message \''+who+'\' remains \''+msg+'\''
        else :
            msg = 'Unknown first character in message '+msg
        # log something
        self.log (msg)

    #
    # api to higher level layers
    # 
    def register_callback (self, system, order, device, callback):
        if self.callbacks is None :
            self.callbacks={}
        # generate callback key
        k = unicode(system)+'-'+unicode(order)+'-'
        if system == self.SYSTEM__LIGHTING:
            if (type(device) is dict) and ('group' in device.keys()):
                k+='G-'+unicode(device['group'])
        if system == self.SYSTEM__TEMP_CONTROL:
            if (type(device) is dict) and ('zone' in device.keys()) and ('sensor' in device.keys()):
                k+='['+unicode(device['zone'])+'-'+unicode(device['sensor'])+']'
        self.callbacks[k] = callback
        #print (unicode(self.callbacks))

    def execute_callback (self, system, order, device, data=None):
        k = unicode(system)+'-'+unicode(order)+'-'
        if system == self.SYSTEM__LIGHTING:
            if (type(device) is dict) and ('group' in device.keys()):
                k+='G-'+unicode(device['group'])
        if system == self.SYSTEM__TEMP_CONTROL:
            if (type(device) is dict) and ('zone' in device.keys()) and ('sensor' in device.keys()):
                k+='['+unicode(device['zone'])+'-'+unicode(device['sensor'])+']'
        if k in self.callbacks.keys() :
            func = self.callbacks[k]
            func (device, data)

    #------------------------------------------------------------------------------------------------------------------
    #
    # message parsers by system, calls appropriate registered callbacks
    #

    # Lighting systems

    def cmd_lighting (self, msg) :
        # light command
        # '*0*#1##'
        m = re.match('^\*(?P<command>[01])\*(?P<light>\d{2,4})##$',msg)
        if m is not None:
            data = m.groupdict()
            self.log (unicode(data))
            device = { 'light': data['light'] }
            self.execute_callback(self.SYSTEM__LIGHTING, data['command'], device, None)
            return
        m = re.match('^\*(?P<command>[01])\*#(?P<group>\d{1,3})##$',msg)
        if m is not None:
            data = m.groupdict()
            self.log (unicode(data))
            device = { 'group': data['group'] }
            self.execute_callback(self.SYSTEM__LIGHTING, data['command'], device, None)
            return
        self.log ('lighting command '+msg)

    # Temperature control systems

    def status_tempcontrol (self, msg) :
        # temperature report
        # '101*0*0270##'
        m = re.match('^\*(?P<probe>\d{3})\*0\*(?P<temperature>\d{4})##$',msg)
        if m is not None:
            data = m.groupdict()
            self.log (unicode(data))
            # generate the device key
            zone = int(data['probe'][0])
            sensor = int(data['probe'][1:])
            device = { 'zone': zone, 'sensor': sensor }
            temp = float(data['temperature'])/10.0
            data = { 'temp': temp, 'unit': '°C' }
            self.execute_callback(self.SYSTEM__TEMP_CONTROL, self.TEMP_CONTROL__REPORT_TEMP, device, data)
            return
        self.log ('temp control status '+msg)

        
    #------------------------------------------------------------------------------------------------------------------
    #
    # system scanning
    #

    def scan_network (self):
        self.scan_socket = myOpenLayer1.OwnSocket(
                config.host,
                config.port,
                config.password,
                myOpenLayer1.OwnSocket.COMMAND)
        # set the callback to get messages from the layer 1
        self.scan_socket.set_ready_callback(self.scan_ready)
        self.scan_socket.set_data_callback(self.scan_read_serials)
        # add the monitor socket to the system loop
        self.system_loop.add_socket(self.scan_socket)

    def scan_ready (self):
        # send the scan request...
        #self.scan_socket.set_data_callback(self.scan_select_device_callback)
        self.devices = []
        self.scan_socket.send("*#1001*0*13##")

    def scan_read_serials (self, msg):
        self.scan_socket.log (msg)
        # parse the *#1001*0*13*[mac address in decimal]## messages
        m = re.match('^\*#1001\*(?P<address>\d+)\*13\*(?P<macaddr>\d+)##$',msg)
        if m is not None:
            data = m.groupdict()
            self.scan_socket.log('mac address '+unicode(data['macaddr']))
            self.devices.append({'system': self.SYSTEM__LIGHTING, 'address': int(data['address']), 'macaddr': int(data['macaddr'])})
            return
        if msg==self.scan_socket.ACK:
            self.scan_socket.log(unicode(self.devices))
            self.current_device = 0
            self.scan_select_device ()

    def scan_select_device (self):
        dev = self.devices[self.current_device]
        self.scan_socket.set_data_callback(self.scan_confirm_selected)
        self.scan_socket.send("*1001*10#"+unicode(dev['macaddr'])+"*0##")

    def scan_confirm_selected (self, msg):
        if msg==self.scan_socket.ACK:
            # request the config to be sent
            self.scan_socket.set_data_callback(self.scan_receive_conf)
            self.scan_socket.send("*#1001*0*38#0##")
        else:
            # in case we don't get an ACK here...              
            dev = self.devices[self.current_device]
            self.scan_socket.log ("ERROR while attempting to select device with ID "+unicode(dev['macaddr']))
            self.scan_finish ()

    def scan_receive_conf (self, msg):
        self.scan_socket.log (msg)
        d = self.devices[self.current_device]
        if 'data' in d.keys():
            v = d['data']
        else:
            v = []
        v.append(msg)
        d['data'] = v
        self.devices[self.current_device] = d

        if msg==self.scan_socket.ACK:
            # end of config data for this device
            self.current_device+=1
            if self.current_device < len(self.devices):
                self.scan_select_device()
            else:
                self.scan_finish()
    
    def scan_finish (self):
        f = open('devices.txt','w')
        f.write (json.dumps(self.devices, indent=4))
        f.close ()
        self.system_loop.remove_socket(self.scan_socket)
        self.scan_socket.close()
