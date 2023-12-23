from datetime import datetime

from .tools import Rqt


"""
fsm.py:
This file contains all classes required to implementate the FSM
"""


#----------------------------------------------------------------------------------------------
class Fsm():
    """
    FSM defines the structure and methods of FSM, it creates and contains all the States that FSM can run

    wd: reference to WD object
    rqt_in: contains the last valid Request to be executed
    fsm_timeout_rqt: represents a signal to indicate to FSM that a state transition has been requested by WD
    fsm_transition_rqt: represents a signal to indicate to FSM that a state transition has to be done, the time of the current State is finish
    list_state: contains all State instances
    """
    def __init__(self, wd):
        self.wd = wd
        self.rqt_in = None
        self.fsm_timeout_rqt = False
        self.fsm_transition_rqt = None
        
        self.list_states = {
            "start" : StateStart(wid = "start", context = self),
            "check" : StateCheck(wid = "check", context = self),
            "run" : StateRun(wid = "run", context = self),
            "sleep" : StateSleep(wid = "sleep", context = self),
            "prelock" : StatePrelock(wid = "prelock", context = self),
            "lock" : StateLock(wid = "lock", context = self),
            "warning" : StateWarning(wid = "warning", context = self),
            "detection" : StateDetection(wid = "detection", context = self),
            "idle" : StateIdle(wid = "idle", context = self),
            "stop" : StateStop(wid = "stop", context = self)
        }

        self.c_state = self.list_states["start"]
        self.n_state = self.list_states["start"]

    def do(self):
        """ run current state routine"""
        rqt_temp = self.wd.get_rqt()
        self.c_state.do(rqt_temp)

    def calculate(self):
        """ calculate next state """               
        self.c_state.calculate()

    def make_transition(self):
        """ perform actions needed to make a state transition """
        time_now = datetime.now()
        self.fsm_transition_rqt = None
        self.fsm_timeout_rqt = False
        if self.c_state != self.n_state:
            print(f"\n>> INFO : Transition to state {self.n_state.wid}")
            self.c_state = self.n_state
            if self.c_state == "lock": self.wd.update_status({"detection_counter": 0})
            self.wd.update_status({"state": self.c_state.wid, "last_time_update_fsm": time_now})
            self.wd.set_rqt(Rqt(sender = self.wd, msg = {"fsm_transition": self.c_state.wid})) # send a request to indicate others Item that a transition has be done
    
    
#----------------------------------------------------------------------------------------------
class States():
    """ 
    State is a interface class to concrete states

    wid: State name
    context: reference context to FSM
    """

    def __init__(self, wid = None, context = None):
        """ ... """
        self.wid = wid
        self.context = context
    
    def do(self, rqt_in):
        """ perform state routine """            
        pass

    def calculate(self):
        """ calculate next state """              
        pass


#---------------------------------------->> START
class StateStart(States):

    def do(self, rqt_in):
        print("> Loading Items")
        for iname, ibox in self.context.wd.boxes.items(): ibox.load_items()
        print("> Setting Items")
        for iname, ibox in self.context.wd.boxes.items(): ibox.setup_items(self.context.wd) 
        print("> Starting Items")
        for iname, ibox in self.context.wd.boxes.items(): ibox.start_items() 

    def calculate(self):
        self.context.n_state = self.context.list_states["check"]


#---------------------------------------->> CHECK
class StateCheck(States):

    def do(self, rqt_in):
        if rqt_in.target.wid == "wilddog" or rqt_in.sender.wid == "wilddog": rqt_in.execute()

    def calculate(self):
        ready_temp = True
        for inode in self.context.wd.boxes["nodes"].items:
            if inode.status["started"] != True: ready_temp = False

        if self.context.fsm_timeout_rqt: self.context.n_state = self.context.list_states["stop"]
        elif ready_temp: self.context.n_state = self.context.list_states["run"]


#---------------------------------------->> RUN
class StateRun(States):

    def do(self, rqt_in):
        if rqt_in.target.wid != None: rqt_in.execute()

    def calculate(self):
        if self.context.fsm_timeout_rqt: self.context.n_state = self.context.list_states["idle"]
        elif self.context.fsm_transition_rqt == "sleep": self.context.n_state = self.context.list_states["sleep"]
        elif self.context.fsm_transition_rqt == "prelock": self.context.n_state = self.context.list_states["prelock"]
            

#---------------------------------------->> SLEEP
class StateSleep(States):

    def do(self, rqt_in):
        if rqt_in.target.wid != None: rqt_in.execute()

    def calculate(self):
        if self.context.fsm_timeout_rqt: self.context.n_state = self.context.list_states["idle"]
        elif self.context.fsm_transition_rqt == "run": self.context.n_state = self.context.list_states["run"] 


#---------------------------------------->> PRELOCK
class StatePrelock(States):

    def do(self, rqt_in):
        if rqt_in.target.wid == "wilddog" or rqt_in.sender.wid == "wilddog": rqt_in.execute()

    def calculate(self):
        if self.context.fsm_timeout_rqt: self.context.n_state = self.context.list_states["lock"]
        elif self.context.fsm_transition_rqt == "run": self.context.n_state = self.context.list_states["run"]


#---------------------------------------->> WARNING
class StateWarning(States):

    def do(self, rqt_in):
        if rqt_in.target.wid == "wilddog" or rqt_in.sender.wid == "wilddog": rqt_in.execute()

    def calculate(self):
        if self.context.fsm_timeout_rqt: self.context.n_state = self.context.list_states["detection"]
        elif self.context.fsm_transition_rqt == "run": self.context.n_state = self.context.list_states["run"]


#---------------------------------------->> LOCK
class StateLock(States):

    def do(self, rqt_in):
        if rqt_in.target.wid == "wilddog" or rqt_in.sender.wid == "wilddog" or rqt_in.command == "send_alert": rqt_in.execute() 

    def calculate(self):
        if self.context.fsm_timeout_rqt: self.context.n_state = self.context.list_states["idle"]
        elif self.context.fsm_transition_rqt == "warning": self.context.n_state = self.context.list_states["warning"]
        elif self.context.fsm_transition_rqt == "detection": self.context.n_state = self.context.list_states["detection"]
        elif self.context.fsm_transition_rqt == "run": self.context.n_state = self.context.list_states["run"]


#---------------------------------------->> DETECTION
class StateDetection(States):

    def do(self, rqt_in):
        if rqt_in.target.wid == "wilddog" or rqt_in.sender.wid == "wilddog": rqt_in.execute()

    def calculate(self):
        if self.context.fsm_timeout_rqt: self.context.n_state = self.context.list_states["idle"]
        elif self.context.fsm_transition_rqt == "idle": self.context.n_state = self.context.list_states["idle"]


#---------------------------------------->> IDLE
class StateIdle(States):

    def do(self, rqt_in):
        if rqt_in.target.wid == "wilddog" or rqt_in.sender.wid == "wilddog": rqt_in.execute()

    def calculate(self):
        if self.context.fsm_timeout_rqt: self.context.n_state = self.context.list_states["run"]
        elif self.context.fsm_transition_rqt == "run": self.context.n_state = self.context.list_states["run"]


#---------------------------------------->> STOP
class StateStop(States):

    def do(self, rqt_in):
        if rqt_in.target.wid != None: rqt_in.execute()

    def calculate(self):
        pass