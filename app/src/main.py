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

    
    async def run_get_data():
        while True:
            self.on_accel_lat_change = await self.Vehicle.Acceleration.Lateral.get()
            self.on_accel_long_change = await self.Vehicle.Acceleration.Longitudinal.get()
            self.on_accel_vert_change = await self.Vehicle.Acceleration.Vertical.get()
            self.on_gps_lat_change = await self.Vehicle.CurrentLocation.Latitude.get()
            self.on_gps_long_change = await self.Vehicle.CurrentLocation.Longitude.get()
            if self.aws_connector.status:
                self.aws_connector.publish_gps_accel_message(self.gps_lat, self.gps_long, self.accel_lat, self.accel_long, self.accel_vert)
            await asyncio.sleep(0.1)


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


    async def on_start_m(self):
        """Run when the vehicle app starts"""
        print("on_start before")
        await self.Vehicle.Acceleration.Lateral.subscribe(self.on_accel_lat_change)
        await self.Vehicle.Acceleration.Longitudinal.subscribe(
            self.on_accel_long_change
        )
        await self.Vehicle.Acceleration.Vertical.subscribe(self.on_accel_vert_change)
        await self.Vehicle.CurrentLocation.Latitude.subscribe(self.on_gps_lat_change)
        await self.Vehicle.CurrentLocation.Longitude.subscribe(self.on_gps_long_change)
        # await self.Vehicle.Speed.subscribe(self.on_speed_change)
        #
        print("on start done")

    async def on_gps_lat_change(self, data: DataPointReply):
        self.gps_lat = data.get(self.Vehicle.CurrentLocation.Latitude).value
        # await self.pub_gps_data()
        # if self.count == 0:
        #     self.pub_gps_data()
        #     self.count += 1
        await self.pub_gps_data()
        # await self.pub_gps_accel_data()



    async def on_gps_long_change(self, data: DataPointReply):
        self.gps_long = data.get(self.Vehicle.CurrentLocation.Longitude).value
        await self.pub_gps_data()
        # await self.pub_gps_accel_data()



    async def on_accel_lat_change(self, data: DataPointReply):
        self.accel_lat = data.get(self.Vehicle.Acceleration.Lateral).value

        await self.pub_accel_data()
        await self.pub_gps_accel_data()


    async def on_accel_long_change(self, data: DataPointReply):
        self.accel_long = data.get(self.Vehicle.Acceleration.Longitudinal).value
        # print("on_accel_long_change")
        # print(self.accel_long)
        await self.pub_accel_data()
        await self.pub_gps_accel_data()


    async def on_accel_vert_change(self, data: DataPointReply):
        self.accel_vert = data.get(self.Vehicle.Acceleration.Vertical).value
        # print("on_accel_vert_change")
        # print(self.accel_vert)
        await self.pub_accel_data()
        await self.pub_gps_accel_data()

    async def pub_accel_data(self):
        if self.aws_connector.status:
            print("pub_accel_data")
            self.aws_connector.publish_message(self.accel_lat, self.accel_long, self.accel_vert)

    async def pub_gps_data(self):
        if self.aws_connector.status:
            self.aws_connector.publish_gps_message(self.gps_lat, self.gps_long)
    
    async def pub_gps_accel_data(self):
        if self.aws_connector.status:
            self.aws_connector.publish_gps_accel_message(self.gps_lat, self.gps_long, self.accel_lat, self.accel_long, self.accel_vert)

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
