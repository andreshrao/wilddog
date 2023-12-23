from .containers import Item


"""
tools.py:
This file contains the Rqt class and others functions 
"""


#----------------------------------------------------------------------------------------------
class Rqt():
    """ 
    Rqt class contains all the information needed to execute a request. 
    
    sender : defines the creator Item
    target : defines the executor target Item
    command : defines the task to be executed
    payload : contains additional information to perform the command
    msg : contains the original message comming from the sender
    
    """

    def __init__(self, sender = Item(), target = Item(), command = None, payload = {}, msg = {}):
        """ ... """
        self.sender = sender
        self.target = target
        self.command = command
        self.payload = payload
        self.msg = msg

    def show(self):
        """ show up the content of request """
        print(f"\n>> RQT \
        \nSENDER : {self.sender.wid} \
        \nTARGET : {self.target.wid} \
        \nCOMMAND : {self.command} \
        \nPAYLOAD : {self.payload} \
        \nMSG : {self.msg}")

    def execute(self):
        """ launch the request execution """
        if self.validate():
            if self.sender.wid != "timer_system": self.show()
            self.target.execute_rqt(self)
        
    def validate(self):
        """ verify that content in request is valid """
        try:
            if self.sender.wid == None: return False
            elif self.target.wid == None: return False
            elif self.command == None: return False
            else: return True
        except:
            return False