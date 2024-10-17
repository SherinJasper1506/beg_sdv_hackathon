https://eclipse-kuksa.github.io/kuksa-website/quickstart/

docker run  -it --rm --net=host ghcr.io/eclipse/kuksa.val/databroker:master --insecure
 
docker run  -it --rm --net=host ghcr.io/eclipse/kuksa.val/databroker-cli:master

docker build -t driver-id . -f ./app/Dockerfile

docker run -it --net=host driver-id
 

pip install kuksa-client

feed Vehicle.Driver.Identifier.Subject 1