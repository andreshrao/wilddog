from datetime import datetime

from .items import ItemTimer
from .tools import Rqt


"""
timers.py:
This file cotains all the implementation classes of Timers
"""


#----------------------------------------------------------------------------------------------
class TimerElement(ItemTimer):
    """
    TimerElemet implements a Timer allowing to watch some Elements and get status information for WD.
    
    feature_onoff: defines the parameter to control group_onoff - turn off Elements with timeout
    feature_door: defines the parameter to watch group_door - Determinate if doors are opened
    feature_window: defines the parameter to watch group_windows - Determinate if all windows are closed
    feature_temperature: defines the parameter to watch group_temperature - Determinate average temperature
    rqt_out : contains all request to submit to WD
    """
    def check(self):
        """ Timer routine """
        now = datetime.now()
        rqt_out = []

        feature_onoff = self.wd.settings["feature_group_onoff"]
        feature_door = self.wd.settings["feature_group_door"]
        feature_window = self.wd.settings["feature_group_window"]
        feature_temperature = self.wd.settings["feature_group_temperature"]

        result_door = True
        result_window = True
        result_temperature = []

        for ielement in self.wd.boxes["elements"].items:
            # TIMEOUT 
            if self.wd.settings["group_onoff"] in ielement.settings["group"] and feature_onoff in ielement.status : 
                if ielement.status["onoff"] == "ON" and ielement.settings["timeout_enable"]:
                    try:
                        delta_time_1 = (now - ielement.status["last_time_on"]).total_seconds() # time Element being ON
                        delta_time_2 = (now - ielement.status["last_time_interaction"]).total_seconds() # time Element being unused
                    except:
                        delta_time_1 = 0
                        delta_time_2 = 0
                    if delta_time_1 > ielement.settings["timeout_value"] and delta_time_2 > ielement.settings["timeout_value"]:
                        rqt_out.append(Rqt(sender = self, target = ielement, command = "set_status", msg = {"onoff": "OFF"}))
                elif ielement.status["onoff"] == "OFF" and ielement.settings["timeout_enable"] != True and ielement.settings["timeout_value"] != None:
                    rqt_out.append(Rqt(sender = self, target = ielement, command = "set_settings", msg = {"timeout_enable": True}))

            # DOOR
            if self.wd.settings["group_door"] in ielement.settings["group"] and feature_door in ielement.status:
                if ielement.status[feature_door] != None: result_door = result_door and ielement.status[feature_door]
                else: result_door = False

            # WINDOW
            if self.wd.settings["group_window"] in ielement.settings["group"] and feature_window in ielement.status:
                if ielement.status[feature_window] != None: result_window = result_window and ielement.status[feature_window]
                else: result_window = False

            # TEMPERATURE
            if self.wd.settings["group_temperature"] in ielement.settings["group"] and feature_temperature in ielement.status:
                if ielement.status[feature_temperature] != None: result_temperature.append(float(ielement.status[feature_temperature]))
                else: pass

        if len(result_temperature) > 0 : result_temperature = sum(result_temperature) / len(result_temperature)
        else: result_temperature = 0

        if self.wd.status["door"] != result_door: rqt_out.append(Rqt(sender = self, target = self.wd, command = "update_door", msg = {"value": result_door}))
        if self.wd.status["window"] != result_window: rqt_out.append(Rqt(sender = self, target = self.wd, command = "update_window", msg = {"value": result_window}))
        if self.wd.status["temperature"] != result_temperature: rqt_out.append(Rqt(sender = self, target = self.wd, command = "update_temperature", msg = {"value": result_temperature}))

        for irqt in rqt_out: self.wd.set_rqt(irqt)


#----------------------------------------------------------------------------------------------
class TimerSystem(ItemTimer):      
    """
    TimerSystem implements the Timer responsible to control and update internal clock in WD, FSM
    timeout transitions, reset detection counter

    c_state: current State name
    rqt_out: contains all request to submit to WD
    """

    def check(self):
        """ ... """
        now = datetime.now()
        c_state = self.wd.fsm.c_state.wid
        rqt_out = []

        # TIME UPDATE
        rqt_out.append(Rqt(sender = self, target = self.wd, command = "update_time", msg = {"value": now}))

        # TIME LIGHT
        time_light = None
        if now.strftime("%H:%M:%S") > self.time_day and now.strftime("%H:%M:%S") < self.time_night: time_light = "day"
        else: time_light = "night"
        if time_light != self.wd.status["timelight"]: rqt_out.append(Rqt(sender = self, command = "update_timelight", msg = {"value": time_light}))
        
        # TIMEOUT DETECTION
        timeout_detection = self.wd.settings["timeout_detection"]
        if timeout_detection != None and c_state == "lock":
            try: delta_time = (now - self.wd.status["last_time_detection"]).total_seconds()
            except: delta_time = 0
            if delta_time > timeout_detection: rqt_out.append(Rqt(sender = self, command = "timeout_detection", msg = {"value": 0}))

        # TIMEOUT FSM
        timeout_state = self.wd.settings["timeout_state"][c_state]
        if timeout_state != None:
            try: delta_time = (now - self.wd.status["last_time_update_fsm"]).total_seconds()
            except: delta_time = 0
            if delta_time > timeout_state: rqt_out.append(Rqt(sender = self, target = self.wd, command = "timeout_fsm", msg = {"value": delta_time}))

        for irqt in rqt_out: self.wd.set_rqt(irqt)