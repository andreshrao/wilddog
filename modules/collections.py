from . import timers
from . import elements
from . import mqtt_devices
from . import nodes
from . import groups
from . import rules


"""
collections.py :
This file contains lists of all existing Item class constructors. Boxes uses these lists to built Items.
If a new class is created must be also be included in one of these lists
"""


#----------------------------------------------------------------------------------------------
timer_classes = [
    timers.TimerElement,
    timers.TimerSystem
]


#----------------------------------------------------------------------------------------------
element_classes = [
    elements.ElementDiscord,
    mqtt_devices.DeviceButton_a01,
    mqtt_devices.DevicePlug_a01,
    mqtt_devices.DeviceRelay_a01,
    mqtt_devices.DeviceRelay_a12,
    mqtt_devices.DeviceRelay_a22,
    mqtt_devices.DeviceRelay_b12,
    mqtt_devices.DeviceRelay_b22,
    mqtt_devices.DeviceRelay_c01,
    mqtt_devices.DeviceRelay_d01,
    mqtt_devices.DeviceKeypad_a06,
    mqtt_devices.DeviceMovement_a01,
    mqtt_devices.DeviceOverture_a01,
    mqtt_devices.DeviceAlarm_a01,
    mqtt_devices.DeviceAlarm_b01,
    mqtt_devices.DeviceLeakwater_a01
]


#----------------------------------------------------------------------------------------------
node_classes = [
    nodes.NodeMQTT,
    nodes.NodeDiscord
]


#----------------------------------------------------------------------------------------------
rule_classes = [
    rules.RuleStandard
]


#----------------------------------------------------------------------------------------------
group_classes = [
    groups.GroupStandard
]