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

import requests
from vehicle import Vehicle, vehicle  # type: ignore
from velocitas_sdk.util.log import (  # type: ignore
    get_opentelemetry_log_factory,
    get_opentelemetry_log_format,
)

from velocitas_sdk.vehicle_app import VehicleApp
from velocitas_sdk.vdb.reply import DataPointReply
from aws_connecter import AwsConnector


# Configure the VehicleApp logger with the necessary log config and level.
logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("DEBUG")
logger = logging.getLogger(__name__)



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
        # asyncio.create_task(self.on_start_m())
        asyncio.create_task(self.start_aws())
        asyncio.create_task(self.run_get_data())
        # asyncio.create_task(self.test_while())
        # asyncio.create_task(self.test_while2()

    
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
            if self.aws_connector.status:
                self.aws_connector.publish_gps_accel_message(self.gps_lat, self.gps_long, self.accel_lat, self.accel_long, self.accel_vert, current_time)
            if self.check_for_event1(self.accel_vert):
                self.aws_connector.publish_event1_message(self.gps_lat, self.gps_long, self.accel_lat, self.accel_long, self.accel_vert, current_time)
            await asyncio.sleep(0.1)

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
