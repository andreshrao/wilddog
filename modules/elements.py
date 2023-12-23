from copy import copy

from .items import ItemElement
from .tools import Rqt


"""
elements.py:
This file cotains all the implementation classes of Elements
"""


#----------------------------------------------------------------------------------------------
class ElementMqttDevice(ItemElement):
    """
    ElementMqttDevice implements a type of Element use it to communicate on mqtt with external devices
    """

    def handle_in(self, msg = {}, option = {}):
        """ this method handle incomming messages """
        msg_temp = None
        target_temp = None
        command_temp = None

        msg_temp = self.replace_features(msg = msg, replace_type = "input") # replace the external name parameters to the local name parameters
        if "command" in msg_temp: 
            command_temp = msg_temp["command"]
            msg_temp.pop("command")
        if "target" in msg_temp: 
            target_temp = msg_temp["target"]
            msg_temp.pop("target")
        else : target_temp = "wilddog"

        self.update_features(msg_temp) # update element status with incoming message information
        self.wd.set_rqt(Rqt(sender = self, target = self.wd.get_item(target_temp), command = command_temp, msg = msg_temp)) # submit request

    def handle_out(self, msg = {}, option = {}):
        """ This method adapt the outcoming message to the specific Node """
        if not "msg_type" in option: option["msg_type"] = "set"
        msg_temp = self.replace_features(msg = msg, replace_type = "output") # replace local name parameters to external name parameters
        if msg_temp != {} and self.node.wid != None : self.node.send_msg(sid = self.settings["sid"], msg_type = option["msg_type"], msg = msg_temp)

    def execute_rqt(self, rqt_in):
        """ First, Element try to execute command using a common command (on super() class), if not, it will use specific commands """
        if super().execute_rqt(rqt_in): return 
        if rqt_in.command == "set_status": # set_status is a command trying to change the status of Element, so maybe a order has to be send to the external element
            msg = copy(rqt_in.payload)
            if self.settings["onoff_enable"] and "onoff" in msg: # if the request is trying to change the status onoff but this status is already updated, do not execute this command
                if msg["onoff"] == self.status["onoff"]: msg.pop("onoff")
            self.handle_out(msg = msg) # send message
            

#----------------------------------------------------------------------------------------------
class ElementDiscord(ItemElement):
    """
    ElementDiscord implements a type of Element use it to communicate with a discord bot
    """

    def handle_in(self, msg = {}, option = {}):
        """ ... """
        rqt_temp = Rqt()
        msg_temp = None
        target_temp = None
        command_temp = None

        msg_temp = self.replace_features(msg = msg, replace_type = "input")
        if "command" in msg_temp: 
            command_temp = msg_temp["command"]
            msg_temp.pop("command")
        if "target" in msg_temp: 
            target_temp = msg_temp["target"]
            msg_temp.pop("target")
        else : target_temp = "wilddog"

        rqt_temp = Rqt(sender = self, target = self.wd.get_item(wid = target_temp), command = command_temp, msg = msg_temp)

        self.update_features(msg_temp)
        self.wd.set_rqt(rqt_temp)
        if rqt_temp.command == "hello!": self.handle_out(msg = "Hello perrito!")

    def handle_out(self, msg = {}, option = {}):
        """ ... """
        if not "head" in option: option["head"] = ""
        if not "style" in option: option["style"] = None
       
        msg_temp = option["head"]
        if type(msg).__name__ == "dict": # try to adap datas to string
            for ikey, ivalue in msg.items(): msg_temp = msg_temp + f"{ikey}: {ivalue}\n"
        elif type(msg).__name__ == "list": 
            for ivalue in msg: msg_temp = msg_temp + f"{ivalue}\n"
        else: msg_temp = msg_temp + msg

        if msg_temp != "" and self.node.wid != None: self.node.send_msg(msg_temp)

    def execute_rqt(self, rqt_in):
        """ ... """
        if super().execute_rqt(rqt_in): return
        if rqt_in.command == "send_alert": # This command allows Elemento to communicate about important alerts: intrusion, fire/water detection
            msg = copy(rqt_in.payload)
            if "fsm_transition" in msg: 
                msg_temp = "-"
                if msg["fsm_transition"] == "lock": msg_temp = f"INFO : lock state transition :lock:"
                elif msg["fsm_transition"] == "run": msg_temp = f"INFO : run state transition :white_check_mark:"
                elif msg["fsm_transition"] == "detection": msg_temp = f"ALERT: intrution detected :no_entry:"
                self.handle_out(msg = msg_temp)
            if "water_detection" in msg:
                if msg["water_detection"]: msg_temp = f"ALERT: waterleak detected :warning:"
                self.handle_out(msg = msg_temp)
            if "fire_detection" in msg:
                if msg["fire_detection"]: msg_temp = f"ALERT: fire detected :fire:"
                self.handle_out(msg = msg_temp)
 
