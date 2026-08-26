import time
import requests

from gpu_monitor import get_gpu_metrics


SCHEDULER_URL = "http://127.0.0.1:8000"
NODE_ID = 1

HEARTBEAT_INTERVAL = 10


def send_heartbeat():
    gpu_metrics = get_gpu_metrics()

    payload = {
        "gpus": gpu_metrics
    }

    response = requests.post(
        f"{SCHEDULER_URL}/nodes/{NODE_ID}/heartbeat",
        json=payload
    )

    response.raise_for_status()

    print("Heartbeat sent:")
    print(response.json())


def main():
    while True:
        try:
            send_heartbeat()

        except Exception as e:
            print(f"Failed to send heartbeat: {e}")

        time.sleep(HEARTBEAT_INTERVAL)


if __name__ == "__main__":
    main()