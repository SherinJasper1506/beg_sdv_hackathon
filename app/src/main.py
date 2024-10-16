"""A sample skeleton vehicle app."""

import asyncio
import signal
import time

from vehicle import Vehicle, vehicle  # type: ignore
from velocitas_sdk.vehicle_app import VehicleApp


from velocitas_sdk.model import DataPoint
from velocitas_sdk.test.inttesthelper import IntTestHelper

driver_profiles = {
    "Sijil": {"name": "Sijil", "seat_position": 9, "fan_speed": 90, "temp" :22},
    "Raj": {"name": "Rajkumar", "seat_position": 6, "fan_speed": 60,"temp" :21},
    "Sherin": {"name": "Sherin", "seat_position": 5, "fan_speed": 50,"temp" :23},
}

class SampleApp(VehicleApp):
    def __init__(self, vehicle_client: Vehicle):
        # SampleApp inherits from VehicleApp.
        super().__init__()
        self.Vehicle = vehicle_client
        asyncio.create_task(self.run_get_data())

    async def run_get_data(self):
        print("Started.....")
        while True:
            driver_id_obj = await self.Vehicle.Driver.Identifier.Subject.get()
            driver_id = driver_id_obj.value
            try:
                profile = driver_profiles.get(driver_id, None)
                welcome_msg = "Known Driver Profile ID Detected : Welcome, " + profile['name']
                print(welcome_msg)
                await self.set_vss_value_from_signal(self.Vehicle.Speed, 90.0)
                # await self.set_vss_value_from_signal(self.Vehicle.Cabin.Seat.Row1.DriverSide.Position, 9)
                # await self.set_vss_value_from_signal(self.Vehicle.Cabin.HVAC.Station.Row1.Driver.FanSpeed, 90)
                # await self.Vehicle.Cabin.Seat.Row1.DriverSide.Position.set(9)
                # await self.Vehicle.Cabin.HVAC.Station.Row1.Driver.FanSpeed.set(90)
                # await self.Vehicle.Cabin.HVAC.Station.Row1.Driver.Temperature.set(21)
            except Exception as e:
                # logger.error("Unknown profile detected %s", e)
                print(f"Unknown Driver Profile ID {driver_id}")
                await self.set_vss_value_from_signal(self.Vehicle.Speed, 90.0)
                # await self.set_vss_value_from_signal(self.Vehicle.Cabin.Seat.Row1.DriverSide.Position, 0)
                # await self.Vehicle.Cabin.Seat.Row1.DriverSide.Position.set(0)
                # await self.Vehicle.Cabin.HVAC.Station.Row1.Driver.FanSpeed.set(0)
                # await self.Vehicle.Cabin.HVAC.Station.Row1.Driver.Temperature.set(0)
                
            time.sleep(4)

        print("Stopping app")
    
    async def set_vss_value(self, signal_name, signalvalue):
        try:
            inttesthelper = IntTestHelper()
            if isinstance(signalvalue, str):
                response = await inttesthelper.set_string_datapoint(
                    name=signal_name, value=signalvalue
                )
            else:
                response = await inttesthelper.set_float_datapoint(name=signal_name, value=float(signalvalue))
                # response = await inttesthelper.set_int16_datapoint(
                #     name=signal_name, value=int(signalvalue)
                # )
            print("signal name: %s value %s", signal_name, signalvalue)
            print(response)
            return 0
        except Exception as e:
            print("set_vss_value Failed: %s", e)
            return -1
        
    async def set_vss_value_from_signal(self, signal: DataPoint, signalValue):
        await self.set_vss_value(signal.get_path(), signalValue)

async def main():
    """Main function"""
    # logger.info("Starting SampleApp...")
    vehicle_app = SampleApp(vehicle)
    await vehicle_app.run()


LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()

