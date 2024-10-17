"""A sample skeleton vehicle app."""

import asyncio
import signal
import time

from vehicle import Vehicle, vehicle  # type: ignore
from velocitas_sdk.vehicle_app import VehicleApp

from kuksa_client.grpc import VSSClient
from kuksa_client.grpc import Datapoint

driver_profiles = {
    "Sijil": {"name": "Sijil", "seat_position": 9, "fan_speed": 90, "temp" :22},
    "Raj": {"name": "Rajkumar", "seat_position": 6, "fan_speed": 60,"temp" :21},
    "Sherin": {"name": "Sherin", "seat_position": 5, "fan_speed": 50,"temp" :23},
}

class SampleApp(VehicleApp):
    def __init__(self, vehicle_client: Vehicle):
        super().__init__()
        self.Vehicle = vehicle_client
        asyncio.create_task(self.run_get_data())
        
    async def SetVssValues(self,signal_name,data):
        with VSSClient('127.0.0.1', 55555) as client:
            client.set_current_values({
            signal_name: Datapoint(data),
            })
        print("signal name: %s value %s", signal_name, data)

    async def run_get_data(self):
        while True:
            driver_id_obj = await self.Vehicle.Driver.Identifier.Subject.get()
            driver_id = driver_id_obj.value
            try:
                profile = driver_profiles.get(driver_id, None)
                welcome_msg = "Known Driver Profile ID Detected : Welcome, " + profile['name']
                print(welcome_msg)
                await self.SetVssValues('Vehicle.Cabin.Seat.Row1.DriverSide.Position',profile["seat_position"])
                await self.SetVssValues('Vehicle.Cabin.HVAC.Station.Row1.Driver.FanSpeed', profile["fan_speed"])
                await self.SetVssValues('Vehicle.Cabin.HVAC.Station.Row1.Driver.Temperature', profile["temp"])
            except Exception as e:
                print(f"Unknown Driver Profile ID {driver_id}")
                await self.SetVssValues('Vehicle.Cabin.Seat.Row1.DriverSide.Position',0)
                await self.SetVssValues('Vehicle.Cabin.HVAC.Station.Row1.Driver.FanSpeed', 0)
                await self.SetVssValues('Vehicle.Cabin.HVAC.Station.Row1.Driver.Temperature',0)
            time.sleep(4)

async def main():
    """Main function"""
    print("Started.....Driver Identifier Application")
    vehicle_app = SampleApp(vehicle)
    await vehicle_app.run()
    print("Stopping app")


LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()

