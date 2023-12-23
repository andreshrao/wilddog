from datetime import datetime
from copy import copy
import yaml


"""
containers.py :
This file contains classes Item and Box
"""


#----------------------------------------------------------------------------------------------
class Item():
    """
    Item class is a container for components in system, most part of objects inherits from Item

    wid: unique identification name
    type: identification kind (Element, Group, Node, Timer, Rule)
    wd: pointer/context to the main Item system, WD
    status: current status Item
        - error_buffer : error message store
    settings: configuration parameters
        - enable : activate item
        - group: group subscription list
    """

    def __init__(self):
        """ it allows to declare empty attributes. Any configuration must go here """
        self.wid = None
        self.wtype = None
        self.wd = None
        
        self.status = {"error_buffer": []}
        self.settings = {"enable": True, "group": []} 

    def setup(self, wd):
        """ it contains all the configuration routines """
        self.wd = wd

    def start(self, *arg, **kwarg):
        """ it contains all the starging routines """
        pass
    
    def stop(self, *arg, **kwarg):
        """ it contains all the stopping routines """
        pass

    def execute_rqt(self, rqt_in):
        """
        it allows to execute a Request object, here you will find the common Item commands, but 
        every kind of Item can have its own commands. A False is returned if non command is found here. 
        """

        if rqt_in.command == "dummy_command": # dummy_command is a non-action command, any action is executed, but just update last_time_interaction
            self.update_status({"last_time_interaction": datetime.now()})
            return True

        elif rqt_in.command == "set_settings":
            self.update_settings(rqt_in.payload)
            return True
    
        elif rqt_in.command == "get_status" or rqt_in.command == "get_settings": # send back to Sender the status/settings of Target Item
            msg_out = {}
            payload_temp = {}
            if rqt_in.command == "get_status": payload_temp = copy(self.status)
            else: payload_temp = copy(self.settings)
            for ifeature, ivalue in payload_temp.items():
                if type(ivalue).__name__ == "datetime": msg_out[ifeature] =  ivalue.strftime("T%H:%M:%S D%d/%m/%y")
                else: msg_out[ifeature] = ivalue
            rqt_in.sender.handle_out(msg = msg_out)
            return True

        else:
            self.update_status({"last_time_interaction": datetime.now()}) # if any command is found at least last_interaction must be updated, a False is returned
            return False
    
    def update_settings(self, new_settings):
        """ it allows to update only existing parameters in Item.settings"""
        for iparameter, ivalue in new_settings.items():
            if iparameter in self.settings: self.settings[iparameter] = ivalue 
    
    def update_status(self, new_status):
        """ it allows to update/create status parameters"""
        for iparameter, ivalue in new_status.items():
            self.status[iparameter] = ivalue


#----------------------------------------------------------------------------------------------
class Box():
    """
    Box class is a containter for Items. Boxes creates and hosts Items. Boxes allows to load settings
    from the configuration files yaml. Every kind of Item has it own Box

    item_file: file containing all the items to create
    item_collection: class list constructors
    items: created Items 
    """

    def __init__(self, item_file, item_class_collection):
        """ ... """
        self.item_file = item_file
        self.item_class_collection = item_class_collection
        self.items = []

    def load_items(self):
        """ it allows to read configuration file xxxx.yaml to create Items and load Item.settings"""
        yaml_file = open(f"data/{self.item_file}","r")
        yaml_list = yaml.safe_load(yaml_file)
        yaml_file.close()
        for iclass in self.item_class_collection:
            for i_yaml in yaml_list:
                if i_yaml["class"] == iclass.__name__ and i_yaml["settings"]["enable"] :
                    item_temp = iclass()
                    item_temp.wid = i_yaml["wid"]
                    item_temp.update_settings(i_yaml["settings"])
                    self.items.append(item_temp)
    
    def save_items(self):
        """ it allows to save the configuration from Item.settings to configuration file"""
        item_temp = {}
        list_temp = []
        yaml_file = open(f"data/{self.item_file}","w")
        for iitem in self.items:            
            item_temp["class"] = iitem.__class__.__name__
            item_temp["wid"] = iitem.wid
            item_temp["settings"] = iitem.settings
            list_temp.append(copy(item_temp))
        yaml.dump(list_temp, yaml_file, sort_keys = False)
        yaml_file.close()
        print(f"\n>> INFO: Item settings on {self.item_file} saved")

    # def add_item(self, wid, settings, class_type):
    #     pass

    # def remove_item(self, wid):
    #     pass

    def setup_items(self, wd):
        """ setup all items listed"""
        for iitem in self.items: iitem.setup(wd)

    def start_items(self):
        """ start all items listed"""
        for iitem in self.items: iitem.start()

    def stop_items(self):
        """ stop all items listed"""
        for iitem in self.items: iitem.stop()
    
    def get_item(self, wid):
        """ sendback a pointer to a specific Item"""
        if wid != None:
            for iitem in self.items: 
                if iitem.wid == wid: return iitem
        return Item()    