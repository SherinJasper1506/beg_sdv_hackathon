import csv
import time
from aws_connecter import AwsConnector
csv_file_path = "../csv/measurements_run_29_aug.csv"


aws_connector = None
aws_connector = AwsConnector()
aws_connector.start_mqtt()

while not aws_connector.is_ready:
    time.sleep(1)

with open(csv_file_path, 'r') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        # ignore the header row
        if row[0] == "time":
            continue
        print(csv_reader.line_num)
        aws_connector.publish_time_gps_accel_message(row[0], row[1], row[2], row[3], row[4], row[5],
                                                      row[6], row[7], row[8], row[9], row[10], row[11], row[12])
        time.sleep(0.05)