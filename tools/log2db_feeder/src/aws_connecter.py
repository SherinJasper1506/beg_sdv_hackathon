import json
import time
import threading


import paho.mqtt.client as mqtt

THING_NAME = "rcu_lab_2"
SUBSCRIBE_TOPIC = "downloadStatus/" + THING_NAME + "/req"
PUBLISH_TOPIC = "test/data2"
IOT_CORE_ENDPOINT = "a1k4mu7a9eqjbq-ats.iot.eu-central-1.amazonaws.com"
CA_CERT = "./certs/AmazonRootCA1.pem"
CERT_FILE = "./certs/cert_file.pem.crt"
PRIVATE_KEY = "./certs/private_file.pem.key"


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
        self.is_ready = False

    def run_mqtt(self):
        self.__mqtt_client.connect(IOT_CORE_ENDPOINT, 8883, 60)
        self.__mqtt_client.loop_forever()
        while(1):
            time.sleep(1)
            
    
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
        print("subscribing to topic: ", SUBSCRIBE_TOPIC)
        self.status = True
        mqtt_client.subscribe(SUBSCRIBE_TOPIC, qos=0, options=None, properties=None)
        self.mqtt_client = mqtt_client

    def on_disconnect(self, mqtt_client, userdata, rc):
        self.status = False
        print("Disconnected from MQTT broker with result code", rc)
        
    def on_subscribe(self, client, userdata, mid, granted_qos, unkown_arg):
        print("Subscribed")
        self.is_ready = True

    def on_message(self, mqtt_client, userdata, msg):
        payload = msg.payload
        try:
            json_payload = json.loads(payload)
        except json.decoder.JSONDecodeError:
            print("on_mqtt_message: Invalid JSON (most likely programming error)")
            return
        if json_payload["cmd"] == "download_config":
            response = {
                "cmd": "download_config",
                "success": True,
            }
            mqtt_client.publish(PUBLISH_TOPIC, payload=json.dumps(response))


    def publish_time_gps_accel_message(self, time, lat, long, accel_x, accel_y, accel_z, vehicle_wh_f_l,
                                            vehicle_wh_f_r, vehicle_wh_r_l, vehicle_wh_r_r, vehicle_eng_speed, vehicle_speed, manual_event):
        message_json = json.dumps(
            {
                "time": time,
                "lat": lat,
                "long": long,
                "accel_x": accel_x,
                "accel_y": accel_y,
                "accel_z": accel_z,
                "vehicle_wh_f_l": vehicle_wh_f_l,
                "vehicle_wh_f_r": vehicle_wh_f_r,
                "vehicle_wh_r_l": vehicle_wh_r_l,
                "vehicle_wh_r_r": vehicle_wh_r_r,
                "vehicle_eng_speed": vehicle_eng_speed,
                "vehicle_speed": vehicle_speed,
                "manual_event": manual_event,
                "hostname": "rcu_lab"
            }, indent=2
        )
        print(message_json)
        self.mqtt_client.publish(
                topic=PUBLISH_TOPIC,
                payload=message_json)

# aws_connector = AwsConnector()
