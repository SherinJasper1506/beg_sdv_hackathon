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


# Configure the VehicleApp logger with the necessary log config and level.
logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("DEBUG")
logger = logging.getLogger(__name__)
GET_MANUAL_EVENT_TOPIC = "pothole/event1"


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
    
    async def run_get_data(self):
        while True:
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
            self.event_thread = threading.Thread(target=self.calculate_event, args=(data_dict,))
            self.event_thread.start()
            if self.aws_connector.status:
                self.aws_connector.publish_gps_accel_message(data_dict)
            self.event_thread.join()
            await asyncio.sleep(0.02)


    async def calculate_event(self, data_dict):
        # if self.vehicle_speed == 0:
        #     return
        min_val, max_val = self.find_min_max(self._accel_z_arr)
        if max_val - min_val > 0.5:
            return
        vehicle_accel = self.get_vehicle_accel(self.vehicle_speed_avg_arr)
        if not vehicle_accel < -0.2:
            return
        is_vehicle_wh_speed_diff = max(self.vehicle_wh_diff)
        if not is_vehicle_wh_speed_diff:
            return
        if self.aws_connector.status:
            self.aws_connector.publish_event1_message(data_dict)


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
        
        if len(self.vehicle_speed_arr) > 10:
            self.vehicle_speed_arr.pop(0)
        if len(self.vehicle_speed_avg_arr) > 2:
            self.vehicle_speed_avg_arr.pop(0)
        if len(self._accel_z_arr) > 5:
            self._accel_z_arr.pop(0)
        if len(self.vehicle_wh_diff) > 3:
            self.vehicle_wh_diff.pop(0)

    def find_min_max(self, arr):
        if len(arr) <= 5:
            return 0, 0
        min_val = min(arr)
        max_val = max(arr)
        return min_val, max_val
    
    def get_avg(self, arr):
        if len(arr) == 0:
            return 0
        return sum(arr)/len(arr)

    def get_vehicle_accel(self, arr):
        if len(arr) < 2:
            return 0
        return (arr[len(arr)] - arr[len(arr)-1])

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
        self.aws_connector.start_mqtt()


    @subscribe_topic(GET_MANUAL_EVENT_TOPIC)
    async def on_get_event1(self, data: str) -> None:
        print("Received on_get_event1")
        if data == "bump_start":
            self.event_1 = True
        if data == "bump_stop":
            self.event_1 = False

    # async def on_start_m(self):
    #     """Run when the vehicle app starts"""
    #     print("on_start before")
    #     await self.Vehicle.Acceleration.Lateral.subscribe(self.on_accel_lat_change)
    #     await self.Vehicle.Acceleration.Longitudinal.subscribe(
    #         self.on_accel_long_change
    #     )
    #     await self.Vehicle.Acceleration.Vertical.subscribe(self.on_accel_vert_change)
    #     await self.Vehicle.CurrentLocation.Latitude.subscribe(self.on_gps_lat_change)
    #     await self.Vehicle.CurrentLocation.Longitude.subscribe(self.on_gps_long_change)
    #     # await self.Vehicle.Speed.subscribe(self.on_speed_change)
    #     #
    #     print("on start done")

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
