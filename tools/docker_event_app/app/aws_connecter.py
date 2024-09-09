import json
import time
import threading


import paho.mqtt.client as mqtt

THING_NAME = "rcu_test"
SUBSCRIBE_TOPIC = "test/data"
PUBLISH_TEST_EVENT1_TOPIC = "sdv/event1"
IOT_CORE_ENDPOINT = "a1k4mu7a9eqjbq-ats.iot.eu-central-1.amazonaws.com"
CA_CERT = "./certs/AmazonRootCA1.pem"
CERT_FILE = "./certs/cert_file.pem.crt"
PRIVATE_KEY = "./certs/private_file.pem.key"


class AwsConnector:
    def __init__(self):
        print("AwsConnector init")
        self.status = False
        self.__mqtt_client = mqtt.Client(client_id=THING_NAME, protocol=mqtt.MQTTv5)
        self.__mqtt_client.tls_set(
            ca_certs=CA_CERT, certfile=CERT_FILE, keyfile=PRIVATE_KEY
        )
        self.__mqtt_client.on_connect = self.on_connect
        self.__mqtt_client.on_message = self.on_message
        self.__mqtt_client.on_subscribe = self.on_subscribe
        self.mqtt_thread = threading.Thread(target=self.run_mqtt)
        self.mqtt_client = None
        self.__on_msg_cb = None


    def run_mqtt(self):
        self.__mqtt_client.connect(IOT_CORE_ENDPOINT, 8883, 60)
        self.__mqtt_client.loop_forever()
        while(1):
            time.sleep(1)
            
    def set_on_message_callback(self, cb):
        self.__on_msg_cb = cb
    
    def start_mqtt(self):
        self.mqtt_thread.start()

    def on_connect(self, mqtt_client, userdata, flags, rc, properties=None):
        print("connected to endpoint with result code", rc)
        mqtt_client.is_connected = True
        mqtt_client.publish(
            PUBLISH_TEST_EVENT1_TOPIC,
            payload=json.dumps(
                {
                    "cmd": "init",
                }
            ),
        )
        print("subscribing to topic: ", SUBSCRIBE_TOPIC)
        self.status = True
        mqtt_client.subscribe(SUBSCRIBE_TOPIC, qos=0, options=None, properties=None)
        self.mqtt_client = mqtt_client

    def on_disconnect(self, mqtt_client, userdata, rc):
        self.status = False
        print("Disconnected from MQTT broker with result code", rc)
        
    def on_subscribe(self, client, userdata, mid, granted_qos, unkown_arg):
        print("Subscribed")

    def on_message(self, mqtt_client, userdata, msg):
        payload = msg.payload
        if self.__on_msg_cb is not None:
            self.__on_msg_cb(payload)

    def publish_event1_message(self, data_dict):
        print("event registered")
        message_json = json.dumps(data_dict, indent=2)
        self.mqtt_client.publish(
                topic=PUBLISH_TEST_EVENT1_TOPIC,
                payload=message_json)

# aws_connector = AwsConnector()
