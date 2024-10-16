from sdv_model import Vehicle
import plugins
from browser import aio

vehicle = Vehicle()

driver_profiles = {
    1: {"name": "Sijil", "seat_position": 9, "fan_speed": 90, "temp" :22},
    2: {"name": "Rajkumar", "seat_position": 6, "fan_speed": 60,"temp" :21},
    3: {"name": "Sherin", "seat_position": 5, "fan_speed": 50,"temp" :23},
}

print = plugins.Terminal.print
previous_status = False
SLEEP_TIME = 1
print("Started.....")
await vehicle.ChildDetected.set(False)

while True:
    driver_id = await vehicle.DriverProfileID.get()
    if driver_id < 1:
        previous_id = 0
        print("Driver not Identified ...")
        await vehicle.Cabin.Seat.Row1.DriverSide.Position.set(0)
        await vehicle.Cabin.HVAC.Station.Row1.Driver.FanSpeed.set(0)
        await vehicle.Cabin.HVAC.Station.Row1.Driver.Temperature.set(0)
        await vehicle.DriverProfileID.set(0)
        await vehicle.DriverName.set("")
    if driver_id > 0 and previous_id == 0:
        print(f"Driver Profile ID {driver_id}")
        profile = driver_profiles.get(driver_id, None)
        if profile:
            welcome_msg = "Welcome, " + profile['name']
            print(welcome_msg)
            await vehicle.DriverName.set(welcome_msg)
            await vehicle.Cabin.Seat.Row1.DriverSide.Position.set(profile['seat_position'])
            await vehicle.Cabin.HVAC.Station.Row1.Driver.FanSpeed.set(profile['fan_speed'])
            await vehicle.Cabin.HVAC.Station.Row1.Driver.Temperature.set(profile['temp'])
            previous_id = driver_id
        else:
            print("Unknown profile ID")
            await vehicle.Cabin.Seat.Row1.DriverSide.Position.set(0)
            await vehicle.Cabin.HVAC.Station.Row1.Driver.FanSpeed.set(0)
            await vehicle.Cabin.HVAC.Station.Row1.Driver.Temperature.set(0)
        
    await aio.sleep(SLEEP_TIME)


print("Stop blinking")
