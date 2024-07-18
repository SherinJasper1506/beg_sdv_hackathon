import csv
import time
from aws_connecter import AwsConnector
csv_file_path = "../csv/4_07_24_11_52_am.csv"


aws_connector = None
aws_connector = AwsConnector()
aws_connector.start_mqtt()

while not aws_connector.is_ready:
    time.sleep(1)

with open(csv_file_path, 'r') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        # ignore the header row
        if row[0] == "Time":
            continue
        aws_connector.publish_time_gps_accel_message(row[0], row[1], row[2], row[3], row[4], row[5])
        time.sleep(0.1)