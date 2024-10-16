from kuksa_client.grpc import VSSClient
from kuksa_client.grpc import Datapoint

import time

with VSSClient('127.0.0.1', 55555) as client:
        client.set_current_values({
        'Vehicle.Driver.Identifier.Subject': Datapoint("hello"),
        })
        time.sleep(1)
print("Finished.")