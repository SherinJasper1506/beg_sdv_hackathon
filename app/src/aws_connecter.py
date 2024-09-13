import json
import time
import threading


import paho.mqtt.client as mqtt

THING_NAME = "rcu_car"
SUBSCRIBE_TOPIC_test = "test/data1"
SUBSCRIBE_TOPIC_event_2 = "sdv/event2_switch"
SUBSCRIBE_TOPIC_event_2_config = "sdv/event2_config"
SUBSCRIBE_TOPIC_IMMO = "sdv/immo/app"
PUBLISH_TOPIC = "sdk/test/python"
PUBLISH_GPS_TOPIC = "sdv/gps"
PUBLISH_GPS_ACCEL_TOPIC = "sdv/combined"
PUBLISH_EVENT2_TOPIC = "sdv/event2"
PUBLISH_IMMO_TOPIC = "sdv/immo/device"
IOT_CORE_ENDPOINT = "a1k4mu7a9eqjbq-ats.iot.eu-central-1.amazonaws.com"
CA_CERT = "/dist/src/certs/AmazonRootCA1.pem"
CERT_FILE = "/dist/src/certs/cert_file.pem.crt"
PRIVATE_KEY = "/dist/src/certs/private_file.pem.key"


class AwsConnector:
    def __init__(self):
        print("AwsConnector init")
        self.__threads = []
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
        # mqtt_client.publish(
        #     PUBLISH_TOPIC,
        #     payload=json.dumps(
        #         {
        #             "cmd": "init",
        #         }
        #     ),
        # )
        print("subscribing to topic: ", SUBSCRIBE_TOPIC_test)
        self.status = True
        mqtt_client.subscribe(SUBSCRIBE_TOPIC_test, qos=0, options=None, properties=None)
        mqtt_client.subscribe(SUBSCRIBE_TOPIC_event_2, qos=0, options=None, properties=None)
        mqtt_client.subscribe(SUBSCRIBE_TOPIC_event_2_config, qos=0, options=None, properties=None)
        mqtt_client.subscribe(SUBSCRIBE_TOPIC_IMMO, qos=0, options=None, properties=None)
        self.mqtt_client = mqtt_client

    def on_disconnect(self, mqtt_client, userdata, rc):
        self.status = False
        print("Disconnected from MQTT broker with result code", rc)
        
    def on_subscribe(self, client, userdata, mid, granted_qos, unkown_arg):
        print("Subscribed")

    def on_message(self, mqtt_client, userdata, msg):
        payload = msg.payload
        topic = msg.topic
        if self.__on_msg_cb is not None:
            self.__on_msg_cb(payload, topic)

    def publish_gps_accel_message(self, data_dict):
        # print("pub gps and data")
        message_json = json.dumps(data_dict, indent=2
            )
        print(message_json)
        self.mqtt_client.publish(
                topic=PUBLISH_GPS_ACCEL_TOPIC,
                payload=message_json)

    def publish_event2_message(self, data_dict):
        print("event registered")
        message_json = json.dumps(data_dict, indent=2)
        self.mqtt_client.publish(
                topic=PUBLISH_EVENT2_TOPIC,
                payload=message_json)

    def publish_immo_message(self, data_dict):
        print("immo message")
        message_json = json.dumps(data_dict, indent=2)
        self.mqtt_client.publish(
                topic=PUBLISH_IMMO_TOPIC,
                payload=message_json)

# aws_connector = AwsConnector()
