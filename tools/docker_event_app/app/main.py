from aws_connecter import AwsConnector
import json
import time

class eventApp():
    def __init__(self):
        self.accel_lat = 0
        self.accel_long = 0
        self.accel_vert = 0
        self.gps_lat = 0
        self.gps_long = 0
        self.count = 0
        self.vehicle_speed = 0
        self.vehicle_wh_f_l = 0
        self.vehicle_wh_f_r = 0
        self.vehicle_wh_r_l = 0
        self.vehicle_wh_r_r = 0
        self.vehicle_break = 0
        self.vehicle_steering = 0
        self.vehicle_eng_speed = 0
        self.aws_connector = None
        self.aws_connected = False
        self.event_1 = False
        self.vehicle_speed_arr = []
        self.vehicle_speed_avg_arr = []
        self._accel_z_arr = []
        self.vehicle_wh_diff = []
        self.mqtt_client = None

    def start(self):
        print("starting app")
        self.aws_connector = AwsConnector()
        self.aws_connector.set_on_message_callback(self.on_message)
        self.aws_connector.start_mqtt()
        self.mqtt_client = self.aws_connector.mqtt_client
        self.aws_connected = True
        while(1):
            time.sleep(0.05)


    def stop(self):
        self.aws_connector.stop_mqtt()
        self.aws_connected = False

    def on_message(self, payload):
        print("reach on message")
        try:
            json_payload = json.loads(payload)
        except Exception as e:
            print("on_mqtt_message: Invalid JSON (most likely programming error)")
        # print(json_payload)
        self.load_variables(json_payload)
        self.fill_data_arrays()
        data_dict = {}
        # time = int(payload["time"])
        current_time = (int(time.time()*1000) -20)
        self.construct_dict(data_dict, current_time)
        self.calculate_event(data_dict)
    
    def load_variables(self, payload):
        self.accel_lat = float(payload["accel_x"])
        self.accel_long = float(payload["accel_y"])
        self.accel_vert = float(payload["accel_z"])
        self.gps_lat = float(payload["lat"])
        self.gps_long = float(payload["long"])
        self.vehicle_speed = float(payload["vehicle_speed"])
        self.vehicle_wh_f_l = float(payload["vehicle_wh_f_l"])
        self.vehicle_wh_f_r = float(payload["vehicle_wh_f_r"])
        self.vehicle_wh_r_l = float(payload["vehicle_wh_r_l"])
        self.vehicle_wh_r_r = float(payload["vehicle_wh_r_r"])
        self.vehicle_eng_speed = float(payload["vehicle_eng_speed"])
        

    def fill_data_arrays(self):
        self.vehicle_speed_arr.append(self.vehicle_speed)
        self._accel_z_arr.append(self.accel_vert)
        speed_avg = self.get_avg(self.vehicle_speed_arr)
        self.vehicle_speed_avg_arr.append(speed_avg)
        if self.vehicle_wh_f_l == self.vehicle_wh_f_r and self.vehicle_wh_f_l == self.vehicle_wh_r_l and self.vehicle_wh_f_l == self.vehicle_wh_r_r:
            self.vehicle_wh_diff.append(0)
        else:
            self.vehicle_wh_diff.append(1)
        
        if len(self.vehicle_speed_arr) > 10:
            self.vehicle_speed_arr.pop(0)
        if len(self.vehicle_speed_avg_arr) > 2:
            self.vehicle_speed_avg_arr.pop(0)
        if len(self._accel_z_arr) > 5:
            self._accel_z_arr.pop(0)
        if len(self.vehicle_wh_diff) > 3:
            self.vehicle_wh_diff.pop(0)   

    def find_min_max(self, arr):
        if len(arr) < 5:
            return 0, 0
        min_val = min(arr)
        max_val = max(arr)
        return min_val, max_val
    
    def get_avg(self, arr):
        if len(arr) == 0:
            return 0
        return sum(arr)/len(arr)

    def get_vehicle_accel(self, arr):
        if len(arr) < 2 :
            return 0
        print(len(arr))
        return (arr[len(arr)-1] - arr[len(arr)-2])
    
    def calculate_event(self, data_dict):
        # if self.vehicle_speed == 0:
        #     return
        min_val, max_val = self.find_min_max(self._accel_z_arr)
        if  max_val - min_val < 0.4:
            print(self._accel_z_arr)
            print(max_val)
            print(min_val)
            print(max_val-min_val)
            print("return at accel_z check")
            return
        vehicle_accel = self.get_vehicle_accel(self.vehicle_speed_avg_arr)
        if vehicle_accel > -0.2:
            print("return at speed check")
            return
        is_vehicle_wh_speed_diff = max(self.vehicle_wh_diff)
        if not is_vehicle_wh_speed_diff:
            print("return at wh diff check")
            return
        if self.aws_connector.status:
            sample_dict = {"event": "event1"}
            try:
                self.aws_connector.publish_event1_message(data_dict)
            except Exception as e:
                print("data dict")
                print(data_dict)
                print(e)

    def construct_dict(self, data_dict, current_time):
        data_dict['time'] = current_time
        data_dict['lat'] = self.gps_lat
        data_dict['long'] = self.gps_long
        data_dict['accel_x'] = self.accel_lat
        data_dict['accel_y'] = self.accel_long
        data_dict['accel_z'] = self.accel_vert
        data_dict['vehicle_speed'] = self.vehicle_speed
        data_dict['vehicle_wh_f_l'] = self.vehicle_wh_f_l
        data_dict['vehicle_wh_f_r'] = self.vehicle_wh_f_r
        data_dict['vehicle_wh_r_l'] = self.vehicle_wh_r_l
        data_dict['vehicle_wh_r_r'] = self.vehicle_wh_r_r
        # data_dict['vehicle_break'] = self.vehicle_break
        data_dict['vehicle_eng_speed'] = self.vehicle_eng_speed
        data_dict['hostname'] = "rcu_car"

print("run app")
event_app = eventApp()
event_app.start()
