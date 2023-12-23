from datetime import datetime

from .collections import timer_classes, element_classes, rule_classes, node_classes, group_classes
from .items import ItemSystem
from .machine import Fsm
from .containers import Box
from .tools import Rqt


"""
systems.py
This file contains the implementation for the main system class
"""


#----------------------------------------------------------------------------------------------
class SystemWilddog(ItemSystem):
    """
    SystemWilddog is a singleton class necessary to create the WD item. Here all other Items
    will be created in Boxes. This class contains all the main transversal parameters/context for 
    others Items and for the FSM

    fsm: FSM instance
    rqt_buffer: request queue
    boxes: dict of Item Boxes
    settings:
        - group_onoff: Group name for the Elements that can be turned on/off
        - group_door: Group name for the Elements that has to be considered like a door
        - group_window: Group name for the Elements that has to be considered like a window
        - group_temperature: Group name for the Elements that can send information about temperature
        - feature_group_onoff: Feature name to control/read group_onoff
        - feature_group_door: Feature name to control/read group_door
        - feature_group_window: Feature name to control/read group_window
        - feature_group_temperature: Feature name to control/read group_temperature
        - detection_threshold: How many detections has to be done to declare an intrusion (detection counter threshold)
        - timeout_detection: Defines the maximun time between detection before reset the detection counter
        - timeout_state: contains a dictionry describing the timeout for every State in FSM 
    status:
        - state: current State name
        - time: local time
        - date: local date
        - timelight: defines it is day or night
        - door: door status
        - window: windows status
        - temperature: average temperature
        - detection_counter: number of detections (can be reset by TimerSystem)
        - last_time_update_fsm: Defines the last time when was updated
        - last_time_detection: Defines the last time when a detection was occured
    """

    __instance = None
    __initialized = False

    def __new__(self):
        """ singleton creation """
        if self.__instance == None: self.__instance = super().__new__(self)
        return self.__instance    

    def __init__(self):
        """ ... """
        if self.__initialized: return 
        else: self.__initialized = True
        super().__init__()

        self.fsm = Fsm(self)
        self.rqt_buffer = []
        
        self.boxes = {
            "systems": Box("systems.yaml", [self.__class__]),
            "timers": Box("timers.yaml", timer_classes),
            "elements": Box("elements.yaml", element_classes),
            "rules": Box("rules.yaml", rule_classes),
            "nodes": Box("nodes.yaml", node_classes),
            "groups": Box("groups.yaml", group_classes)
        }

        self.settings = self.settings | {
            "group_onoff" : None,
            "group_door" : None,
            "group_window" : None,
            "group_temperature" : None,
            "feature_group_onoff" : None,
            "feature_group_door" : None,
            "feature_group_window" : None,
            "feature_group_temperature" : None,
            "detection_threshold": None,
            "timeout_detection": None,
            "timeout_state": {}            
        }

    def setup(self, wd):
        """ ... """
        super().setup(wd)
        self.update_status({
            "state": self.fsm.c_state.wid,
            "time": None,
            "date": None,
            "timelight": "day",
            "door": False,
            "window": False,
            "temperature": None,
            "detection_counter": 0,
            "last_time_update_fsm": None,
            "last_time_detection": None
        }) 

    def set_rqt(self, rqt_in):
        """ it allows to submit a new request """
        for irule in self.boxes["rules"].items:
            rqt_temp = irule.check(rqt_in)
            if rqt_temp.validate(): self.rqt_buffer.append(rqt_temp)

    def get_rqt(self):
        """ it allows FSM to get the last valid request in queeu """
        rqt_temp = Rqt()
        if len(self.rqt_buffer) > 0:
            rqt_temp = self.rqt_buffer[0]
            self.rqt_buffer.pop(0)
        return rqt_temp

    def get_item(self, wid = None, box = None):
        """ it allows to get a pointer to a specific Item """
        item_temp = None
        if wid == "wilddog": return self
        if box in self.boxes: item_temp = self.boxes[box].get_item(wid)
        else:
            for iname, ibox in self.boxes.items():
                item_temp = ibox.get_item(wid)
                if item_temp.wid != None: break       
        return item_temp

    def execute_rqt(self, rqt_in):
        """ ... """
        if not "value" in rqt_in.payload : rqt_in.payload["value"] = None
        
        if super().execute_rqt(rqt_in): return

        if rqt_in.command == "timeout_fsm": # request FSM transition if timeout
            self.fsm.fsm_timeout_rqt = True

        elif rqt_in.command == "timeout_detection": # request reset detection counter if timeout last detection
            self.update_status({"detection_counter": rqt_in.payload["value"]})
        
        elif rqt_in.command == "update_fsm": # request FSM transition
            self.fsm.fsm_transition_rqt = rqt_in.payload["state"]

        elif rqt_in.command == "update_time": 
            self.update_status({"time": rqt_in.payload["value"].strftime("%H:%M:%S"), "date": rqt_in.payload["value"].strftime("%d/%m/%y")})

        elif rqt_in.command == "update_timelight": 
            self.update_status({"timelight":rqt_in.payload["value"]})
        
        elif rqt_in.command == "update_door": 
            self.update_status({"door":rqt_in.payload["value"]})

        elif rqt_in.command == "update_window":
            self.update_status({"window":rqt_in.payload["value"]})

        elif rqt_in.command == "update_temperature":
            self.update_status({"temperature":rqt_in.payload["value"]})

        elif rqt_in.command == "update_settings": # request to save configuration Items, for a single Box or all
            if rqt_in.payload["value"] in self.boxes:
                self.boxes[rqt_in.payload["value"]].save_items()
            else:
                for iname, ibox in self.boxes.items(): ibox.save_items()

        elif rqt_in.command == "detection_event" and rqt_in.sender.settings["detection_enable"]: # declare a detection, only Element wich a detection_enable True will be considered
            detection_counter = self.status["detection_counter"] + rqt_in.payload["value"]
            if detection_counter >= self.settings["detection_threshold"]:
                self.fsm.fsm_transition_rqt = "detection"
                self.update_status({"detection_counter": 0, "last_time_detection": datetime.now()})
            else: self.update_status({"detection_counter": detection_counter, "last_time_detection": datetime.now()})

        elif rqt_in.command == "get_list": # get back a list of all Item names
            if rqt_in.payload["value"] in self.boxes:
                msg_temp = [ item.wid for item in self.wd.boxes[rqt_in.payload["value"]].items] 
                rqt_in.sender.handle_out(msg_temp)
            else: return

        # -- DEBUG --
        elif rqt_in.command == "command_test":
            print("\n>> COMMAND TEST WILDDOG :) ")
            if rqt_in.payload["value"] == 1:
                print(f"STATUS WILDDOG: {self.status}")
                print(f"SETTINGS WILDDOG: {self.settings}")
            elif rqt_in.payload["value"] == 2:
                print("Value 2 has been sent")
            elif rqt_in.payload["value"] == 3:
                print("Value 3 has been sent")