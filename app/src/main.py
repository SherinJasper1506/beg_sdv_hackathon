# Copyright (c) 2022-2024 Contributors to the Eclipse Foundation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""A sample skeleton vehicle app."""

import asyncio
import json
import logging
import signal
import time
from datetime import datetime
import threading

import requests
from vehicle import Vehicle, vehicle  # type: ignore
from velocitas_sdk.util.log import (  # type: ignore
    get_opentelemetry_log_factory,
    get_opentelemetry_log_format,
)

from velocitas_sdk.vehicle_app import VehicleApp, subscribe_topic
from velocitas_sdk.vdb.reply import DataPointReply
from aws_connecter import AwsConnector
from aws_connecter import SUBSCRIBE_TOPIC_IMMO


# Configure the VehicleApp logger with the necessary log config and level.
logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("DEBUG")
logger = logging.getLogger(__name__)
GET_MANUAL_EVENT_TOPIC = "pothole/event1"
IMMO_ECU_TOPIC = "immo/ECU/cmd"
IMMO_CLOUD_TOPIC = "immo/cloud/cmd"


class SampleApp(VehicleApp):
    def __init__(self, vehicle_client: Vehicle):
        # SampleApp inherits from VehicleApp.
        super().__init__()
        self.Vehicle = vehicle_client
        self.accel_lat = 0
        self.accel_long = 0
        self.accel_vert = 0
        self.gps_lat = 0
        self.gps_long = 0
        self.aws_connector = None
        self.aws_connected = False
        self.count = 0
        self.vehicle_speed = 0
        self.vehicle_wh_f_l = 0
        self.vehicle_wh_f_r = 0
        self.vehicle_wh_r_l = 0
        self.vehicle_wh_r_r = 0
        self.vehicle_break = 0
        self.vehicle_steering = 0
        asyncio.create_task(self.start_aws())
        asyncio.create_task(self.run_get_data())
        self.event_1 = False
        self.vehicle_speed_arr = []
        self.vehicle_speed_avg_arr = []
        self._accel_z_arr = []
        self.vehicle_wh_diff = []
        self.mqtt_client = None
        self.event2_run = False
        self.event2_config = {"accel_z_threshold" : 0.4, "vehicle_accel_threshold" : -0.2, "accel_window" : 20}
        self.data_push = True
        # Check further
        self.immo_data_push = False
        self.immo_state = ""
    
    async def run_get_data(self):
        while True:
            if self.immo_data_push:
                await asyncio.create_task(self.publish_event(IMMO_ECU_TOPIC, self.immo_state))
                self.immo_data_push = False
            accel_lat_obj = await self.Vehicle.Acceleration.Lateral.get()
            accel_long_obj = await self.Vehicle.Acceleration.Longitudinal.get()
            accel_vert_obj = await self.Vehicle.Acceleration.Vertical.get()
            lat_obj = await self.Vehicle.CurrentLocation.Latitude.get()
            long_obj = await self.Vehicle.CurrentLocation.Longitude.get()
            current_time = (int(time.time()*1000) -20)
            self.accel_lat = accel_lat_obj.value
            self.accel_long = accel_long_obj.value
            self.accel_vert = accel_vert_obj.value
            self.gps_lat = lat_obj.value
            self.gps_long = long_obj.value
            await self.get_can_data()
            data_dict = {}
            self.fill_data_arrays()
            self.construct_dict(data_dict, current_time)
            self.event_thread = None
            if self.event2_run:
                self.event_thread = threading.Thread(target=self.calculate_event, args=(data_dict,))
                self.event_thread.start()
            if self.aws_connector.status:
                pass
               if self.data_push:
                   self.aws_connector.publish_gps_accel_message(data_dict)
            if self.event_thread:
                self.event_thread.join()
            await asyncio.sleep(0.02)


    def calculate_event(self, data_dict):
        min_val, max_val = self.find_min_max(self._accel_z_arr)
        if  max_val - min_val < self.event2_config.get("accel_z_threshold"):
            return
        vehicle_accel = self.get_vehicle_accel(self.vehicle_speed_avg_arr)
        if vehicle_accel > -self.event2_config.get("vehicle_accel_threshold"):
            return
        is_vehicle_wh_speed_diff = max(self.vehicle_wh_diff)
        if not is_vehicle_wh_speed_diff:
            return
        if self.aws_connector.status:
            try:
                print("event2")
                self.aws_connector.publish_event2_message(data_dict)
            except Exception as e:
                print(e)


    async def get_can_data(self):
        self.set_can_default_values()
        try:
            vehicle_speed_obj = await self.Vehicle.Speed.get()
            vehicle_wh_f_l_obj = await self.Vehicle.Chassis.Axle.Row1.Wheel.Left.Speed.get()
            vehicle_wh_f_r_obj = await self.Vehicle.Chassis.Axle.Row1.Wheel.Right.Speed.get()
            vehicle_wh_r_l_obj = await self.Vehicle.Chassis.Axle.Row2.Wheel.Left.Speed.get()
            vehicle_wh_r_r_obj = await self.Vehicle.Chassis.Axle.Row2.Wheel.Right.Speed.get()
            # vehicle_break_obj = self.Vehicle.Body.Lights.Brake.IsActive.get()
            vehicle_eng_speed_obj = await self.Vehicle.OBD.EngineSpeed.get()
            self.vehicle_speed = vehicle_speed_obj.value
            self.vehicle_wh_f_l = vehicle_wh_f_l_obj.value
            self.vehicle_wh_f_r = vehicle_wh_f_r_obj.value
            self.vehicle_wh_r_l = vehicle_wh_r_l_obj.value
            self.vehicle_wh_r_r = vehicle_wh_r_r_obj.value
            # self.vehicle_break = vehicle_break_obj.value
            self.vehicle_eng_speed = vehicle_eng_speed_obj.value
        except Exception as e:
            print(e)
            print("Error in getting CAN data")

    def fill_data_arrays(self):
        self.vehicle_speed_arr.append(self.vehicle_speed)
        self._accel_z_arr.append(self.accel_vert)
        speed_avg = self.get_avg(self.vehicle_speed_arr)
        self.vehicle_speed_avg_arr.append(speed_avg)
        if self.vehicle_wh_f_l == self.vehicle_wh_f_r and self.vehicle_wh_f_l == self.vehicle_wh_r_l and self.vehicle_wh_f_l == self.vehicle_wh_r_r:
            self.vehicle_wh_diff.append(0)
        else:
            self.vehicle_wh_diff.append(1)
        
        if len(self.vehicle_speed_arr) > self.event2_config["accel_window"]:
            self.vehicle_speed_arr.pop(0)
        if len(self.vehicle_speed_avg_arr) > 2:
            self.vehicle_speed_avg_arr.pop(0)
        if len(self._accel_z_arr) > 5:
            self._accel_z_arr.pop(0)
        if len(self.vehicle_wh_diff) > 3:
            self.vehicle_wh_diff.pop(0)   

    def find_min_max(self, arr):
        if len(arr) < 5:
            return 0, 0
        min_val = min(arr)
        max_val = max(arr)
        return min_val, max_val
    
    def get_avg(self, arr):
        if len(arr) == 0:
            return 0
        return sum(arr)/len(arr)

    def get_vehicle_accel(self, arr):
        if len(arr) < 2 :
            return 0
        print(len(arr))
        return (arr[len(arr)-1] - arr[len(arr)-2])

    def construct_dict(self, data_dict, current_time):
        data_dict['time'] = current_time
        data_dict['lat'] = self.gps_lat
        data_dict['long'] = self.gps_long
        data_dict['accel_x'] = self.accel_lat
        data_dict['accel_y'] = self.accel_long
        data_dict['accel_z'] = self.accel_vert
        data_dict['vehicle_speed'] = self.vehicle_speed
        data_dict['vehicle_wh_f_l'] = self.vehicle_wh_f_l
        data_dict['vehicle_wh_f_r'] = self.vehicle_wh_f_r
        data_dict['vehicle_wh_r_l'] = self.vehicle_wh_r_l
        data_dict['vehicle_wh_r_r'] = self.vehicle_wh_r_r
        # data_dict['vehicle_break'] = self.vehicle_break
        data_dict['vehicle_eng_speed'] = self.vehicle_eng_speed
        data_dict['hostname'] = "rcu_car"
        data_dict['event1'] = self.event_1

    def set_can_default_values(self):
        self.vehicle_speed = -1
        self.vehicle_wh_f_l = -1
        self.vehicle_wh_f_r = -1
        self.vehicle_wh_r_l = -1
        self.vehicle_wh_r_r = -1
        # self.vehicle_break = 0
        self.vehicle_eng_speed = -1

    def check_for_event1(self, accel_vert):
        if accel_vert > 1.10:
            return True
        return False


    def post_to_firebase(self, latitude, longitude, accelerometer_vert_value):
        timestamp = round(datetime.now().timestamp() * 1000)
        url = (
            "https://maps-firebase-project-default-rtdb.asia-southeast1.firebasedatabase.app/clicks/"
            + str(timestamp)
            + ".json"
        )
        payload = json.dumps(
            {"lat": latitude, "lng": longitude, "weight": accelerometer_vert_value}
        )
        r = requests.put(url, data=payload)
        print(r)
        return r.status_code

    async def start_aws(self):
        self.aws_connector = AwsConnector()
        self.aws_connector.set_on_message_callback(self.on_message)
        self.aws_connector.start_mqtt()


    @subscribe_topic(GET_MANUAL_EVENT_TOPIC)
    async def on_get_event1(self, data: str) -> None:
        print("Received on_get_event1")
        if data == "bump_start":
            self.event_1 = True
        if data == "bump_stop":
            self.event_1 = False

    @subscribe_topic(IMMO_CLOUD_TOPIC)
    async def on_get_immo_state(self, data: str) -> None:
        print("Received on_get_immo_state")
        if data == "Lock":
            msg = {'locked': True}
        if data == "Unlock":
            msg = {'locked': False}
        if self.aws_connector.status:
            self.aws_connector.publish_immo_message(msg)
            print("publish state to immo")



    def on_message(self, payload, topic):
        print(topic)
        try:
            if topic == "sdv/event2_switch":
                json_payload = json.loads(payload)
                if json_payload["status"] == "start":
                    self.event2_run = True
                if json_payload["status"] == "stop":
                    self.event2_run = False
                if json_payload["cloud"] == "start":
                    self.data_push = True
                if json_payload["cloud"] == "stop":
                    self.data_push = False
            if topic == "sdv/event2_config":
                json_payload = json.loads(payload)
                self.event2_config["accel_z_threshold"] = json_payload["accel_z_threshold"]
                self.event2_config["vehicle_accel_threshold"] = json_payload["vehicle_accel_threshold"]
                self.event2_config["accel_window"] = json_payload["vehicle_wh_speed_diff"]
                print(self.event2_config)
            if topic == SUBSCRIBE_TOPIC_IMMO:
                json_payload = json.loads(payload)
                print(json_payload)
                if json_payload["locked"] == False:
                    # asyncio.create_task(self.publish_event(IMMO_ECU_TOPIC,'Unlock'))
                    self.immo_state = 'Unlock'
                if json_payload["locked"] == True:
                    self.immo_state = 'Lock'
                    # asyncio.create_task(self.publish_event(IMMO_ECU_TOPIC,'Lock'))
                self.immo_data_push = True
        except Exception as e:
            print("Error in on_message")
            print(e)

            

async def main():
    """Main function"""
    logger.info("Starting SampleApp...")
    # Constructing SampleApp and running it.
    vehicle_app = SampleApp(vehicle)
    await vehicle_app.run()


LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()


# export SDV_MIDDLEWARE_TYPE="native"
# export SDV_VEHICLEDATABROKER_ADDRESS="grpc://localhost:55555"


