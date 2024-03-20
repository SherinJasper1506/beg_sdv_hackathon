import json

import paho.mqtt.client as mqtt

THING_NAME = "docker-test"
SUBSCRIBE_TOPIC = "downloadStatus/" + THING_NAME + "/req"
PUBLISH_TOPIC = "downloadStatus/" + THING_NAME + "/res"
IOT_CORE_ENDPOINT = "a1k4mu7a9eqjbq-ats.iot.ap-south-1.amazonaws.com"
CA_CERT = "./certs/AmazonRootCA1.pem"
CERT_FILE = "./certs/cert_file.pem.crt"
PRIVATE_KEY = "./certs/private_file.pem.key"
DOWNLOAD_PATH = "./data"
TEMP_DOWNLOAD_PATH = "./data"
STATUS_FILE_PATH = "./data"
DOWNLOAD_CHUNK_SIZE = 3000000
INSTALLATION_TIMEOUT_SECONDS = 120
MODE = "test"  # change on gateway


class AwsConnector:
    def __init__(self):
        print("OtaDownloader init")
        self.__threads = []
        self.__mqtt_client = mqtt.Client(client_id=THING_NAME, protocol=mqtt.MQTTv5)
        self.__mqtt_client.tls_set(
            ca_certs=CA_CERT, certfile=CERT_FILE, keyfile=PRIVATE_KEY
        )
        self.__mqtt_client.on_connect = self.on_connect
        self.__mqtt_client.on_message = self.on_message
        self.__mqtt_client.on_subscribe = self.on_subscribe
        self.__mqtt_client.connect(IOT_CORE_ENDPOINT, 8883, 60)
        self.__mqtt_client.loop_forever()

    def on_connect(self, mqtt_client, userdata, flags, rc, properties=None):
        print("connected to endpoint with result code", rc)
        mqtt_client.is_connected = True
        mqtt_client.publish(
            PUBLISH_TOPIC,
            payload=json.dumps(
                {
                    "cmd": "init",
                }
            ),
        )
        print("subscribing to topic: ", SUBSCRIBE_TOPIC)
        mqtt_client.subscribe(SUBSCRIBE_TOPIC, qos=0, options=None, properties=None)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribed")

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


aws_connector = AwsConnector()
