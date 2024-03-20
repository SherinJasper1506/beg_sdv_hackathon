import asyncio
import csv

from velocitas_sdk.test.inttesthelper import IntTestHelper


def read_csv_and_format(filename):
    signals = None
    reader = None
    with open(filename, "r") as file:
        reader = csv.reader(file)
        signals = next(reader)
        rows = list(reader)
    return (signals, rows)


async def main():
    inttesthelper = IntTestHelper()
    print(f"{inttesthelper} can be used when your app compiles succesfully!")
    signals, rows = read_csv_and_format(
        "/workspaces/beg_sdv_hackathon/app/mock_data_feeder/gps_data_mock.csv"
    )
    for row in rows:
        for signal, value in zip(signals, row):
            print(signals)
            print(row)
            await inttesthelper.set_double_datapoint(name=signal, value=float(value))
            # have a sleep of 1 sec
            await asyncio.sleep(1)
    print("gps data published")

    # Enable if mock values are needed for testing

    # print("Accel Values")
    # signals, rows = read_csv_and_format(
    #     "/workspaces/beg_sdv_hackathon/app/mock_data_feeder/accel_data_mock.csv"
    # )
    # for row in rows:
    #     for signal, value in zip(signals, row):
    #         print(signals)
    #         print(row)
    #         await inttesthelper.set_float_datapoint(name=signal, value=float(value))
    #         # have a sleep of 1 sec
    #         await asyncio.sleep(1)
    # print("accel data published")


if __name__ == "__main__":
    asyncio.run(main())
