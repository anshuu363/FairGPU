import os
import subprocess


def get_gpu_metrics():

    if os.getenv("MOCK_GPU", "false").lower() == "true":
        return get_mock_gpu_metrics()

    return get_nvidia_gpu_metrics()


def get_nvidia_gpu_metrics():

    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,utilization.gpu,"
            "memory.used,memory.total",
            "--format=csv,noheader,nounits"
        ],
        capture_output=True,
        text=True,
        check=True
    )

    gpus = []

    for line in result.stdout.strip().split("\n"):

        values = [
            value.strip()
            for value in line.split(",")
        ]

        gpu_index = int(values[0])
        utilization = float(values[1])
        memory_used = float(values[2])
        memory_total = float(values[3])

        memory_utilization = (
            memory_used / memory_total
        ) * 100

        gpus.append({
            "gpu_index": gpu_index,
            "utilization_percent": utilization,
            "memory_utilization_percent": memory_utilization,
            "memory_used_gb": memory_used / 1024
        })

    return gpus


def get_mock_gpu_metrics():

    return [
        {
            "gpu_index": 0,
            "utilization_percent": 25,
            "memory_utilization_percent": 30,
            "memory_used_gb": 7.2
        },
        {
            "gpu_index": 1,
            "utilization_percent": 5,
            "memory_utilization_percent": 10,
            "memory_used_gb": 2.4
        }
    ]

def get_gpu_info():

    if os.getenv("MOCK_GPU", "false").lower() == "true":
        return get_mock_gpu_info()

    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total",
            "--format=csv,noheader,nounits"
        ],
        capture_output=True,
        text=True,
        check=True
    )

    gpus = []

    for line in result.stdout.strip().split("\n"):

        values = [
            value.strip()
            for value in line.split(",")
        ]

        gpus.append({
            "gpu_index": int(values[0]),
            "model": values[1],
            "memory_gb": round(float(values[2]) / 1024)
        })

    return gpus


def get_mock_gpu_info():

    return [
        {
            "gpu_index": 0,
            "model": "Mock GPU",
            "memory_gb": 24
        },
        {
            "gpu_index": 1,
            "model": "Mock GPU",
            "memory_gb": 24
        }
    ]