import os
import time
import requests
from gpu_monitor import get_gpu_metrics, get_gpu_info
from gpu_monitor import get_gpu_metrics


SCHEDULER_URL = os.getenv(
    "SCHEDULER_URL",
    "http://127.0.0.1:8000"
)

HEARTBEAT_INTERVAL = int(
    os.getenv("HEARTBEAT_INTERVAL", "10")
)


def send_heartbeat(node_id):

    gpu_metrics = get_gpu_metrics()

    payload = {
        "gpus": gpu_metrics
    }

    response = requests.post(
        f"{SCHEDULER_URL}/nodes/{node_id}/heartbeat",
        json=payload,
        timeout=5
    )

    response.raise_for_status()

    print("Heartbeat sent:")
    print(response.json())


def main():

    print("Node Agent starting...")
    print(f"Scheduler: {SCHEDULER_URL}")
    node_id = register_node()

    register_gpus(node_id)

    while True:

        try:
            send_heartbeat(node_id)

        except Exception as e:
            print(f"Failed to send heartbeat: {e}")

        time.sleep(HEARTBEAT_INTERVAL)
    
def register_node():

    hostname = os.uname().nodename

    payload = {
        "name": hostname,
        "hostname": hostname
    }

    response = requests.post(
        f"{SCHEDULER_URL}/nodes/register",
        json=payload,
        timeout=5
    )

    response.raise_for_status()

    node = response.json()

    print("Node registered:")
    print(node)

    return node["id"]

def register_gpus(node_id):

    gpus = get_gpu_info()

    for gpu in gpus:

        response = requests.post(
            f"{SCHEDULER_URL}/nodes/{node_id}/gpus",
            json=gpu,
            timeout=5
        )

        response.raise_for_status()

        print("GPU registered:")
        print(response.json())
if __name__ == "__main__":
    main()


