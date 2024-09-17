import csv
import time
from aws_connecter import AwsConnector
csv_file_path = "../csv/sept_9-sorted.csv"


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
        current_time = int(time.time() * 1000)
        print(csv_reader.line_num, row[0], row[12])
        event1 = False
        if(row[12]== "0.0"):
            event1 = False
        else:
            event1 = True
        aws_connector.publish_time_gps_accel_message(current_time, row[1], row[2], row[3], row[4], row[5],
                                                      row[6], row[7], row[8], row[9], row[10], row[11], event1)
        time.sleep(0.1)