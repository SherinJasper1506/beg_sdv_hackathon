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

from vehicle import Vehicle, vehicle  # type: ignore
from velocitas_sdk.util.log import (  # type: ignore
    get_opentelemetry_log_factory,
    get_opentelemetry_log_format,
)
from velocitas_sdk.vdb.reply import DataPointReply
from velocitas_sdk.vehicle_app import VehicleApp, subscribe_topic

# Configure the VehicleApp logger with the necessary log config and level.
logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("DEBUG")
logger = logging.getLogger(__name__)

GET_SPEED_REQUEST_TOPIC = "sampleapp/getSpeed"
GET_SPEED_RESPONSE_TOPIC = "sampleapp/getSpeed/response"
DATABROKER_SUBSCRIPTION_TOPIC = "sampleapp/currentSpeed"

GET_ACCEL_REQUEST_TOPIC = "sampleapp/getAccel"
GET_ACCEL_RESPONSE_TOPIC = "sampleapp/getAccel/response"
ACCEL_DATABROKER_SUBSCRIPTION_TOPIC = "sampleapp/accelData"

GET_GPS_REQUEST_TOPIC = "sampleapp/getGps"
GET_GPS_RESPONSE_TOPIC = "sampleapp/getGps/response"
GPS_DATABROKER_SUBSCRIPTION_TOPIC = "sampleapp/gpsData"


class SampleApp(VehicleApp):
    def __init__(self, vehicle_client: Vehicle):
        # SampleApp inherits from VehicleApp.
        super().__init__()
        self.Vehicle = vehicle_client
        self.accel_lat = 0
        self.accel_long = 0
        self.accel_vert = 0
        # self.aws_connector = AwsConnector()
        self.gps_lat = 0
        self.gps_long = 0

    async def on_start(self):
        """Run when the vehicle app starts"""
        # This method will be called by the SDK when the connection to the
        # Vehicle DataBroker is ready.
        # Here you can subscribe for the Vehicle Signals update (e.g. Vehicle Speed).
        await self.Vehicle.Acceleration.Lateral.subscribe(self.on_accel_lat_change)
        await self.Vehicle.Acceleration.Longitudinal.subscribe(
            self.on_accel_long_change
        )
        await self.Vehicle.Acceleration.Vertical.subscribe(self.on_accel_vert_change)
        await self.Vehicle.CurrentLocation.Latitude.subscribe(self.on_gps_lat_change)
        await self.Vehicle.CurrentLocation.Longitude.subscribe(self.on_gps_long_change)
        await self.Vehicle.Speed.subscribe(self.on_speed_change)

    async def on_gps_lat_change(self, data: DataPointReply):
        self.gps_lat = data.get(self.Vehicle.CurrentLocation.Latitude).value
        await self.publish_event(
            GPS_DATABROKER_SUBSCRIPTION_TOPIC,
            json.dumps({"gps_lat": self.gps_lat, "gps_long": self.gps_long}),
        )

    async def on_gps_long_change(self, data: DataPointReply):
        self.gps_long = data.get(self.Vehicle.CurrentLocation.Longitude).value
        await self.publish_event(
            GPS_DATABROKER_SUBSCRIPTION_TOPIC,
            json.dumps({"gps_lat": self.gps_lat, "gps_long": self.gps_long}),
        )

    async def on_accel_lat_change(self, data: DataPointReply):
        self.accel_lat = data.get(self.Vehicle.Acceleration.Lateral).value
        await self.publish_event(
            ACCEL_DATABROKER_SUBSCRIPTION_TOPIC,
            json.dumps(
                {
                    "accel_lat": self.accel_lat,
                    "accel_long": self.accel_long,
                    "accel_vert": self.accel_vert,
                }
            ),
        )

    async def on_accel_long_change(self, data: DataPointReply):
        self.accel_long = data.get(self.Vehicle.Acceleration.Longitudinal).value
        await self.publish_event(
            ACCEL_DATABROKER_SUBSCRIPTION_TOPIC,
            json.dumps(
                {
                    "accel_lat": self.accel_lat,
                    "accel_long": self.accel_long,
                    "accel_vert": self.accel_vert,
                }
            ),
        )

    async def on_accel_vert_change(self, data: DataPointReply):
        self.accel_vert = data.get(self.Vehicle.Acceleration.Vertical).value
        await self.publish_event(
            ACCEL_DATABROKER_SUBSCRIPTION_TOPIC,
            json.dumps(
                {
                    "accel_lat": self.accel_lat,
                    "accel_long": self.accel_long,
                    "accel_vert": self.accel_vert,
                }
            ),
        )

    async def on_speed_change(self, data: DataPointReply):
        """The on_speed_change callback, this will be executed when receiving a new
        vehicle signal updates."""
        # Get the current vehicle speed value from the received DatapointReply.
        # The DatapointReply containes the values of all subscribed DataPoints of
        # the same callback.
        vehicle_speed = data.get(self.Vehicle.Speed).value

        # Do anything with the received value.
        # Example:
        # - Publishes current speed to MQTT Topic (i.e. DATABROKER_SUBSCRIPTION_TOPIC).
        await self.publish_event(
            DATABROKER_SUBSCRIPTION_TOPIC,
            json.dumps({"speed": vehicle_speed}),
        )

    @subscribe_topic(GET_SPEED_REQUEST_TOPIC)
    async def on_get_speed_request_received(self, data: str) -> None:
        """The subscribe_topic annotation is used to subscribe for incoming
        PubSub events, e.g. MQTT event for GET_SPEED_REQUEST_TOPIC.
        """

        # Use the logger with the preferred log level (e.g. debug, info, error, etc)
        logger.debug(
            "PubSub event for the Topic: %s -> is received with the data: %s",
            GET_SPEED_REQUEST_TOPIC,
            data,
        )

        # Getting current speed from VehicleDataBroker using the DataPoint getter.
        vehicle_speed = (await self.Vehicle.Speed.get()).value

        # Do anything with the speed value.
        # Example:
        # - Publishes the vehicle speed to MQTT topic (i.e. GET_SPEED_RESPONSE_TOPIC).
        await self.publish_event(
            GET_SPEED_RESPONSE_TOPIC,
            json.dumps(
                {
                    "result": {
                        "status": 0,
                        "message": f"""Current Speed = {vehicle_speed}""",
                    },
                }
            ),
        )

    @subscribe_topic(GET_ACCEL_REQUEST_TOPIC)
    async def on_get_accel_request_received(self, data: str) -> None:
        """The subscribe_topic annotation is used to subscribe for incoming
        PubSub events, e.g. MQTT event for GET_ACCEL_REQUEST_TOPIC.
        """
        logger.debug(
            "PubSub event for the Topic: %s -> is received with the data: %s",
            GET_ACCEL_REQUEST_TOPIC,
            data,
        )

        # Getting current speed from VehicleDataBroker using the DataPoint getter.
        self.accel_lat = (await self.Vehicle.Acceleration.Lateral.get()).value
        self.accel_long = (await self.Vehicle.Acceleration.Longitudinal.get()).value
        self.accel_vert = (await self.Vehicle.Acceleration.Vertical.get()).value

        await self.publish_event(
            GET_ACCEL_RESPONSE_TOPIC,
            json.dumps(
                {
                    "result": {
                        "status": 0,
                        "message": f"""Accel Lat = {self.accel_lat},Accel Long = {self.accel_long},Accel Vert = {self.accel_vert}""",
                    },
                }
            ),
        )

    @subscribe_topic(GET_GPS_REQUEST_TOPIC)
    async def on_get_gps_request_received(self, data: str) -> None:
        logger.debug(
            "PubSub event for the Topic: %s -> is received with the data: %s",
            GET_GPS_REQUEST_TOPIC,
            data,
        )
        self.gps_lat = (await self.Vehicle.CurrentLocation.Latitude.get()).value
        self.gps_long = (await self.Vehicle.CurrentLocation.Longitude.get()).value

        await self.publish_event(
            GET_GPS_RESPONSE_TOPIC,
            json.dumps(
                {
                    "result": {
                        "status": 0,
                        "message": f"""Gps Lat = {self.gps_lat},Gps Long = {self.gps_long}""",
                    },
                }
            ),
        )


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
