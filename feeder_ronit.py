import asyncio

from velocitas_sdk.test.inttesthelper import IntTestHelper


async def main():
    inttesthelper = IntTestHelper()
    print(f"{inttesthelper} can be used when your app compiles succesfully!")
    response = await inttesthelper.set_float_datapoint(
        name="Vehicle.Acceleration.Lateral", value=3.3
    )
    response = await inttesthelper.set_float_datapoint(
        name="Vehicle.Acceleration.Longitudinal", value=4.3
    )
    response = await inttesthelper.set_float_datapoint(
        name="Vehicle.Acceleration.Vertical", value=5.3
    )
    print("published")


if __name__ == "__main__":
    asyncio.run(main())
