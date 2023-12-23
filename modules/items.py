from datetime import datetime
from copy import copy
from threading import Thread
import time

from .containers import Item
from .tools import Rqt


"""
items.py:
This file contains father classes for every kind of Item (Group, Elements, Node, Rules, Timers).
"""


#----------------------------------------------------------------------------------------------
class ItemSystem(Item):
    """
    ItemSystem defines run() method and the execution of FSM
    """
    
    def __init__(self):
        """ ... """
        super().__init__()
        self.wtype = "system"

    def run(self):
        """ This is the main routine of WD, responsible to execute the FSM"""
        print(f"\n----- WILDDOG v0.100 -----\n")
        while(1):
            self.fsm.do()   # performe actions for the current state
            self.fsm.calculate()    # calculate next state
            self.fsm.make_transition()  # make transition to next state if needed   

#----------------------------------------------------------------------------------------------
class ItemTimer(Item):
    """
    ItemTimer defines the base configuration for timer including the thread object setup

    time_day: sunrise time
    time_night: sunset time
    _timer_thread: object to load thread 
    settings:
        - period : prediod of main routine check()
    """
    def __init__(self):
        """ ... """
        super().__init__()
        self.wtype = "timer"
        self.time_day = None
        self.time_night = None
        self._timer_thread = None

        self.settings = self.settings | {
            "period": None
        } 

    def setup(self, wd):
        """ initialize variables and point _timer_thread to _launch_thread"""
        super().setup(wd)
        self.time_day = "08:30:00"
        self.time_night = "17:00:00"
        self._timer_thread = Thread(target=self._launch_thread,daemon=True)

    def start(self):
        """ start check() """
        self._timer_thread.start()
    
    def stop(self):
        """ stop check() """
        self._timer_thread.stop()

    def check(self, *arg, **kwarg):
        """ it contains the main periodic routine """
        pass  

    def _launch_thread(self):
        """ this method just define the periodic execution of check()"""
        while True:
            if self.settings["enable"]: self.check()
            time.sleep(self.settings["period"]) 


#----------------------------------------------------------------------------------------------
class ItemElement(Item):
    """
    ItemElement defines the base method to handle incoming and outcoming messages for Elements. Also the base
    status parameters

    features: describes the relationship between external name parameters and local name parameters (to Wilddog)
    node: points to the Node that Element use to communicate externally
    settings:
        - onoff_enable: Element can be turned on/off
        - battery_enable: Element has a battery
        - timeout_enable: Element should be turned off automatically after timeout_value seconds
        - detection_enable: Element can declare a detection
        - timeout_value: value of timeout in seconds
        - node: node name
        - sid: Element name that Node will use in external services (wid and sid can be the same)
    status:
        - last_time_connexion : last time when Element made a request, last incoming communication
        - last_time_interaction : last time when someone sent a message to Element
    """

    def __init__(self):
        """ ... """
        super().__init__()
        self.wtype = "element"
        self.features = {}
        self.node = None

        self.settings = self.settings | {
            "onoff_enable": False,
            "battery_enable": False,
            "timeout_enable": True,
            "detection_enable": False,
            "timeout_value": None,
            "node": None,
            "sid": None
        }

    def handle_in(self, msg = {}, option = {}):
        """ it defines the process that Element has to perform when message is recived from its Node """
        pass

    def handle_out(self, msg = {}, option = {}):
        """ it defines the process that Element has to perform when a message has to be sent to Node """
        pass

    def setup(self, wd):
        """ ... """
        super().setup(wd)
        time_now = datetime.now()

        self.update_status({
            "error_buffer": [],
            "last_time_connexion": None,
            "last_time_interaction": time_now
        })
        
        if self.settings["onoff_enable"]: self.update_status({"onoff": None, "last_time_on": None, "last_time_off": None})
        if self.settings["battery_enable"]: self.update_status({"battery": None})

        self.node = self.wd.get_item(wid = self.settings["node"], box = "nodes")
        if self.node.wid == None: self.status["error_buffer"].append("node_failed")

    def update_features(self, msg):
        """ this method is used to update status of Element using the last message comming from Node """
        time_now = datetime.now()
        msg_temp = copy(msg)
        if self.settings["onoff_enable"] and "onoff" in msg_temp:
            if self.status["onoff"] != "ON" and msg_temp["onoff"] == "ON": msg_temp["last_time_on"] = time_now
            if self.status["onoff"] != "OFF" and msg_temp["onoff"] == "OFF": msg_temp["last_time_off"] = time_now
        self.update_status(msg_temp | {"last_time_connexion":time_now})
    
    def replace_features(self, msg = {}, replace_type = None):
        """ replace external name parameter to local name parameter or viceversa """
        msg_temp = {}
        for iparameter, ivalue in msg.items():
            if replace_type == "input" and iparameter in self.features:
                msg_temp[self.features[iparameter]] = ivalue
            elif replace_type == "output" and iparameter in [jvalue for jfeature, jvalue in self.features.items()]:
                for jfeature, jvalue in self.features.items():
                    if iparameter == jvalue: msg_temp[jfeature] = ivalue
            else: msg_temp[iparameter] = ivalue
        return msg_temp            


#----------------------------------------------------------------------------------------------
class ItemRule(Item):
    """
    This class defines the check() method for Rules, wich allows system to validate or not a request

    sender: Pointer to Item who creates the request to validate
    target: Pointer to Item responsible to execute the request to validate
    settings:
        - sender: name of sender
        - target: name of target
        - condition: contains the conditions to validate the request
        - command: task to execute by the target
        - payload: additional information used to execute the command
    """

    def __init__(self):
        """ ... """
        super().__init__()
        self.wtype = "rule"
        self.sender = None
        self.target = None

        self.settings = self.settings | {
            "sender": None,
            "target": None,
            "condition": [],
            "command": None,
            "payload": {}
        }

    def setup(self, wd):
        """ ... """
        super().setup(wd)

        self.sender = self.wd.get_item(wid = self.settings["sender"])
        self.target = self.wd.get_item(wid = self.settings["target"])

        self.status["error_buffer"] = []
        if self.sender.wid == None: 
            self.status["error_buffer"].append("items_failed")
            self.settings["enable"] = False

    def check(self, rqt_in):
        """ this method is responsible to evaluate a incomming requests and modify the request if necessary"""
        rqt_out = Rqt()
        condition_ok = True
        if self.settings["enable"] and (self.sender == rqt_in.sender or self.sender.wid in rqt_in.sender.settings["group"]): # is sender in request the same of the rule or share they the same group? this will trigger the condition evaluation
            # CONDITIONS
            for icondition in self.settings["condition"]:
                condition_temp = False
                if icondition["item"] == "this_item": # "this_item" means the condition must be evaluated using the local status of Sender, otherwise the Item idicated
                    msg_temp = rqt_in.msg
                    condition_temp = self._evaluate_condition(icondition, msg_temp) # submit the evaluation of condition once the item and its status are stablished
                else:     
                    element_temp = self.wd.get_item(wid = icondition["item"]) 
                    if element_temp.wid != None:
                        msg_temp = element_temp.status
                        condition_temp = self._evaluate_condition(icondition, msg_temp)
                    else:
                        condition_temp = False
                condition_ok = condition_ok and condition_temp # all conditions in the Rule must to be True to validate the Rule
            #REPLACE RQT
            if condition_ok: # if all conditions are okay, the final request must be settled, using first the parameters in the Rulem if not defined, use so those in the original request 
                rqt_out = copy(rqt_in)
                if self.settings["target"] != None: rqt_out.target = self.target 
                if self.settings["target"] == "this_item": rqt_out.target = rqt_out.sender
                if self.settings["command"] != None: rqt_out.command = self.settings["command"]
                if self.settings["payload"] != {}: rqt_out.payload = self.settings["payload"]
                else: rqt_out.payload = rqt_in.msg
        return rqt_out

    def _evaluate_condition(self, condition, msg):
        """ this method evaluate a single condition, checking a single feature in the incoming message"""
        condition_ok = False
        feature = condition["feature"]
        if feature in msg:
            value = condition["value"]
            operator = condition["operator"]
            try:
                if msg[feature] == value and operator == "=": condition_ok = True
                elif msg[feature] != value and operator == "!=": condition_ok = True
                elif msg[feature] > value and operator == ">": condition_ok = True
                elif msg[feature] < value and operator == "<": condition_ok = True 
            except:
                condition_ok = False       
        else:
            condition_ok = False
        return condition_ok 


#----------------------------------------------------------------------------------------------
class ItemNode(Item):
    """
    ItemNode defines the base methods to create a Node, including the configuration of thread

    elements: pointers to the Items menbers
    _node_thread: object to load thread 
    settings:
        - elements: Element names list
    status:
        - started: indicate if Node has been correctly started
    """

    def __init__(self):
        """ ... """
        super().__init__()
        self.wtype = "node"
        self.elements = []
        self._node_thread = None

        self.settings = self.settings | {
            "elements": []
        }

    def setup(self, wd):
        """ ... """
        super().setup(wd)
        self.elements = []
        self._node_thread = Thread(target=self._launch_thread,daemon=True)

        self.update_status({
            "error_buffer": [],
            "started": False
        })

        for ielement in self.settings["elements"]: # load pointers to every Element using this Node
            element_temp = self.wd.get_item(wid = ielement["wid"], box = "elements")
            if element_temp.wid != None: 
                self.elements.append(element_temp)
                element_temp.update_settings({"node":self.wid,"sid":ielement["sid"]})
                element_temp.setup(wd)
            else:
                self.status["error_buffer"].append(f"element_failed_{ielement}")

    def start(self):
        """ start Node thread """
        self._node_thread.start()

    def stop(self):
        """ stop Node thread """
        self._node_thread.stop()

    def set_msg(self, *arg, **kwarg):
        """ This method is used to handle all new incoming message"""
        pass

    def send_msg(self, *arg, **kwarg):
        """ This method is used to send message through the Node, just Element menbers can use it """
        pass

    def _launch_thread(self, *arg, **kwarg):
        """ This method is used to start the Node"""
        pass


#----------------------------------------------------------------------------------------------
class ItemGroup(Item):
    """
    ItemGroup defines the methods to configurate Groups

    elements: pointers to the Items menbers
    settings:
        - elements: Element names list
    """

    def __init__(self):
        """ ... """
        super().__init__()
        self.wtype = "group"
        self.elements = []

        self.settings = self.settings | {
            "elements": []
        } 

    def setup(self, wd):
        """ ... """
        super().setup(wd)
        self.elements = []
        for ielement in self.settings["elements"]: # load pointers to every Element menber
            element_temp = self.wd.get_item(wid = ielement)
            if element_temp.wid != None and element_temp.settings["enable"]:   
                self.elements.append(element_temp)
                if not self.wid in element_temp.settings["group"]: 
                    element_temp.update_settings({"group": element_temp.settings["group"]+[self.wid]})
                    element_temp.setup(wd)
            else:
                self.status["error_buffer"].append(f"element_failed_{ielement}")
    
    def execute_rqt(self, rqt_in):
        """ ... """
        if "grouptarget" in rqt_in.payload : # if parameter "grouptarget" is present in the payload, it means the command goes to the Group itself and not its menbers
            super().execute_rqt(rqt_in) 
        else:
            for ielement in self.elements: ielement.execute_rqt(rqt_in)
            