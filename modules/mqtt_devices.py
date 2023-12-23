from .elements import ElementMqttDevice


"""
mqtt_devices.py:
This file cotains specific implementation classes of ElementMqttDevice
"""


#----------------------------------------------------------------------------------------------
class DeviceButton_a01(ElementMqttDevice):
    def __init__(self):
        """ simple button """
        super().__init__()
        self.features = self.features | {
            "action": "event",
            "battery_level": "battery",
            "device_temperature": "temperature"
        }
        

#----------------------------------------------------------------------------------------------
class DevicePlug_a01(ElementMqttDevice): 
    def __init__(self):
        """ plug """
        super().__init__()
        self.features = self.features | {
            "state": "onoff",
            "power": "power"
        }


#---------------------------------------------------------------------------------------------- 
class DeviceRelay_a01(ElementMqttDevice): 
    def __init__(self):
        """ relay 1 chanel with neutral """
        super().__init__()
        self.features = self.features | {
            "state": "onoff"
        }

                           
#----------------------------------------------------------------------------------------------
class DeviceRelay_a12(ElementMqttDevice): 
    def __init__(self):
        """ relay 2 chanel with neutral CH1 """
        super().__init__()
        self.features = self.features | {
            "state_l1": "onoff"
        }


#----------------------------------------------------------------------------------------------
class DeviceRelay_a22(ElementMqttDevice): 
    def __init__(self):
        """ relay 2 chanel with neutral CH2 """
        super().__init__()
        self.features = self.features | {
            "state_l2": "onoff"
        }


#----------------------------------------------------------------------------------------------
class DeviceRelay_b12(ElementMqttDevice): 
    def __init__(self):
        """ relay 2 chanel without neutral CH1 """
        super().__init__()
        self.features = self.features | {
            "state_right": "onoff"
        }


#----------------------------------------------------------------------------------------------
class DeviceRelay_b22(ElementMqttDevice): 
    def __init__(self):
        """ relay 2 chanel without neutral CH2 """
        super().__init__()
        self.features = self.features | {
            "state_left": "onoff"
        }


#----------------------------------------------------------------------------------------------
class DeviceRelay_c01(ElementMqttDevice): 
    def __init__(self):
        """ relay 1 chanel """
        super().__init__()
        self.features = self.features | {
            "state": "onoff"
        }


#----------------------------------------------------------------------------------------------
class DeviceRelay_d01(ElementMqttDevice): 
    def __init__(self):
        """ power relay 1 chanel 32A """
        super().__init__()
        self.features = self.features | {
            "state": "onoff"
        }


#----------------------------------------------------------------------------------------------
class DeviceMovement_a01(ElementMqttDevice):
    def __init__(self):
        """ movement sensor """
        super().__init__()
        self.features = self.features | {
            "occupancy": "detection",
            "battery_level": "battery"
        }


#----------------------------------------------------------------------------------------------
class DeviceOverture_a01(ElementMqttDevice):
    def __init__(self):
        """ contact sensor """
        super().__init__()
        self.features = self.features | {
            "contact": "contact",
            "battery_level": "battery",
            "device_temperature": "temperature"
        }


#----------------------------------------------------------------------------------------------
class DeviceKeypad_a06(ElementMqttDevice):
    def __init__(self):
        """ keypad """
        super().__init__()
        self.features = self.features | {
            "action":"event",
            "battery_level": "battery"
        }


#----------------------------------------------------------------------------------------------
class DeviceAlarm_a01(ElementMqttDevice):
    def __init__(self):
        """ alarm fire """
        super().__init__()
        self.features = self.features | {
            "smoke": "fire_detection",
            "battery_level": "battery"
        }


#----------------------------------------------------------------------------------------------
class DeviceAlarm_b01(ElementMqttDevice):
    def __init__(self):
        """ alarm intrusion """
        super().__init__()
        self.features = self.features | {
            "battery_level": "battery"
        }


#----------------------------------------------------------------------------------------------
class DeviceLeakwater_a01(ElementMqttDevice):
    def __init__(self):
        """ leakwater sensor """
        super().__init__()
        self.features = self.features | {
            "water_leak": "water_detection",
            "battery_level": "battery"
        }