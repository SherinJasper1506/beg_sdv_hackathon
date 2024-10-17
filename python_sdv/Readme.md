
## Kuksa KickStart

https://eclipse-kuksa.github.io/kuksa-website/quickstart/

docker run  -it --rm --net=host ghcr.io/eclipse/kuksa.val/databroker:master --insecure
 
docker run  -it --rm --net=host ghcr.io/eclipse/kuksa.val/databroker-cli:master

## Dockers

### Building locally

docker build -t driver-id . -f ./app/Dockerfile

docker run -it --net=host driver-id
 
### Target Device build

The docker container for the target device is built via Github workflow actions.
Make Sure to change the tag before the build

Pull the Arm64 based Docker images from 
https://github.com/SherinJasper1506?tab=packages&repo_name=beg_sdv_hackathon

Pulling Docker :  docker pull ghcr.io/sherinjasper1506/beg_sdv_hackathon_driver_ver_2:arm64

Running Docker : docker run  -it --rm --net=host ghcr.io/sherinjasper1506/beg_sdv_hackathon_driver_ver_2:arm64

## Dependencies:

Python dependencies: refer requirements.txt

apt-get espeak dlib  mosquitto mosquitto-clients

### Error1:

Traceback (most recent call last): 
  File "/dist/src/main.py", line 20, in <module> 
    from vehicle import Vehicle, vehicle  # type: ignore 
  File "/usr/local/lib/python3.10/dist-packages/vehicle/__init__.py", line 8, in <module> 
    from velocitas_sdk.model import ( 
  File "/usr/local/lib/python3.10/dist-packages/velocitas_sdk/model.py", line 24, in <module> 
    from velocitas_sdk import config 
  File "/usr/local/lib/python3.10/dist-packages/velocitas_sdk/config.py", line 49, in <module> 
    _config = Config(__middleware_type) 
  File "/usr/local/lib/python3.10/dist-packages/velocitas_sdk/config.py", line 36, in __init__ 
    self.middleware: Middleware = self.__create_middleware(__middleware) 
  File "/usr/local/lib/python3.10/dist-packages/velocitas_sdk/config.py", line 41, in __create_middleware 
    _middleware = NativeMiddleware() 
  File "/usr/local/lib/python3.10/dist-packages/velocitas_sdk/native/middleware.py", line 34, in __init__ 
    self.pubsub_client = MqttClient(_port, _hostname) 
  File "/usr/local/lib/python3.10/dist-packages/velocitas_sdk/native/mqtt.py", line 47, in __init__ 
    self._sub_client.connect(self._hostname, self._port) 
  File "/usr/local/lib/python3.10/dist-packages/paho/mqtt/client.py", line 914, in connect 
    return self.reconnect() 
  File "/usr/local/lib/python3.10/dist-packages/paho/mqtt/client.py", line 1044, in reconnect 
    sock = self._create_socket_connection() 
  File "/usr/local/lib/python3.10/dist-packages/paho/mqtt/client.py", line 3685, in _create_socket_connection 
    return socket.create_connection(addr, timeout=self._connect_timeout, source_address=source) 
  File "/usr/lib/python3.10/socket.py", line 845, in create_connection 
    raise err 
  File "/usr/lib/python3.10/socket.py", line 833, in create_connection 
    sock.connect(sa) 
ConnectionRefusedError: [Errno 111] Connection refused

### Solution: 
sudo apt update -y && sudo apt install mosquitto mosquitto-clients -y