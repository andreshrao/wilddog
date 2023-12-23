import paho.mqtt.client as mqtt
import json
import discord
from discord.ext import tasks

from .items import ItemNode


"""
nodes.py:
This file contains implemention Node for MQTT and Discord services
"""


#----------------------------------------------------------------------------------------------
class NodeMQTT(ItemNode):
    """ 
    NodeMQTT implements the MQTT Node 

    _mqtt_client: paho object
    settings:
        - adresse : mosquitto ip adresse
        - port : mosquitto port 
    """

    def __init__(self):
        """ ... """
        super().__init__()
        self._mqtt_client = None

        self.settings = self.settings | {
            "adress": None,
            "port": None
        }

    def setup(self, wd):
        """ ... """
        super().setup(wd)
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self._connect_mqtt
        self._mqtt_client.on_message = self.set_msg
        self._mqtt_client.connect(self.settings["adress"],self.settings["port"],60)

    def set_msg(self, client, userdata, msg_in):
        """ ... """
        sid = None
        msg = {}

        try:
            sid = msg_in.topic.split("/")[1]
            msg = json.loads(msg_in.payload)
        except:
            sid = None 
            msg = {}

        if msg != {} and sid != None and sid != "bridge":
            for ielement in self.elements:
                if ielement.settings["sid"] == sid: ielement.handle_in(msg = msg) # if the message is validated by the Node the Element sender has to handle it

    def send_msg(self, sid, msg_type, msg):
        """ ... """
        msg = json.dumps(msg)
        self._mqtt_client.publish(f"zigbee2mqtt/{sid}/{msg_type}", payload=msg, qos=0, retain=False)

    def _launch_thread(self):
        """ ... """
        self._mqtt_client.loop_forever()

    def _connect_mqtt(self, client, userdata, flags, rc):
        """ method to indicate that connection with server was ok """
        if rc == 0:
            self._mqtt_client.subscribe("zigbee2mqtt/#")
            self.update_status({"started": True})
            print("\n>> INFO : node zb succefully connected to mosquitto server")
            
        else:
            print("\n>> INFO : node zb failed connecting to mosquitto server")
            self.status["error_buffer"].append("connexion_failed")


#----------------------------------------------------------------------------------------------
class NodeDiscord(ItemNode):
    """ 
    NodeDiscord implements the Discord Node 

    _discord_client: discord object
    _msg_buffer: outcomming message to Discord
    settings:
        - token : bot token
        - guild : guild name on discord server
    """
    def __init__(self):
        """ ... """
        super().__init__()

        self._intents = discord.Intents.all()
        self._intents.message_content = True
        self._discord_client = discord.Client(intents=self._intents)
        self._msg_buffer = []

        self.settings = self.settings | {
            "token": None,
            "guild": None
        }

    def setup(self, wd):
        """ ... """
        super().setup(wd)
        self._discord_client.on_ready = self._on_ready # set on_ready built-in method for local method
        self._discord_client.on_message = self._on_message # set on_message built-in method for local method

    def set_msg(self, msg_in):
        """ ... """
        msg = {}
        sid = None
        msg_temp = None

        try: # parser message from Discord users
            sid = "discord_bot"
            msg_temp = msg_in.content
            msg_temp = msg_temp.replace(" ", "")
            msg_temp = msg_temp.split("\n")
            for line in msg_temp:
                parameter = line.split(":")
                msg = msg | {parameter[0]:self._convert_type(parameter[1])}
        except:
            msg = {}
            sid = None

        if msg != {} and sid != None:
            for ielement in self.elements:
                if ielement.settings["sid"] == sid: ielement.handle_in(msg = msg)

    def send_msg(self, msg_in):
        """ ... """
        self._msg_buffer.append(msg_in)

    def _launch_thread(self):
        """ ... """
        self._discord_client.run(self.settings["token"], log_handler = None)

    def _convert_type(self, msg_in):
        """" it converts string to numbers/booleans"""
        if msg_in.isnumeric(): return int(msg_in)
        if msg_in == "True" or msg_in == "true": return True
        if msg_in == "False" or msg_in == "false": return False
        return msg_in

    async def _on_ready(self):
        """" connection with server is ok. set some communication server parameters"""
        self._user = self._discord_client.user
        self._guild = discord.utils.get(self._discord_client.guilds, name = self.settings['guild'])
        self._chanel = discord.utils.get(self._guild.channels, name="general")
        self.myloop.start() # sending message to Discord server requires an async function
        self.update_status({"started": True})
        print(f"\n>> INFO : node discord succefully connected to {self._guild.name} server in chanel {self._chanel.name} ")
    
    async def _on_message(self, msg_in):
        """ It receives new incomming messages """
        if msg_in.author != self._user: self.set_msg(msg_in)
        
    @tasks.loop(seconds=0.1)
    async def myloop(self):
        """ loop routine to send messages to Discord server """
        if len(self._msg_buffer) > 0:
            await self._chanel.send(self._msg_buffer[0])
            self._msg_buffer.pop(0)