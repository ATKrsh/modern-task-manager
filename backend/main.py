import asyncio
import psutil
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_system_metrics():
    # CPU
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_freq = psutil.cpu_freq()
    
    # Memory
    mem = psutil.virtual_memory()
    
    # Network (bytes sent/recv since last boot)
    net = psutil.net_io_counters()
    
    # Disk
    disk = psutil.disk_usage('/')
    
    return {
        "timestamp": time.time(),
        "cpu": {
            "percent": cpu_percent,
            "freq_mhz": cpu_freq.current if cpu_freq else 0
        },
        "memory": {
            "percent": mem.percent,
            "used_gb": round(mem.used / (1024**3), 2),
            "total_gb": round(mem.total / (1024**3), 2)
        },
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv
        },
        "disk": {
            "percent": disk.percent,
            "used_gb": round(disk.used / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2)
        }
    }

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    await websocket.accept()
    psutil.cpu_percent(interval=0.1) # Initialize cpu_percent
    try:
        while True:
            metrics = get_system_metrics()
            await websocket.send_json(metrics)
            await asyncio.sleep(1) # Send update every 1 second
    except Exception as e:
        print(f"WebSocket connection closed: {e}")

@app.get("/api/processes")
def get_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            info = proc.info
            mem_mb = round(info['memory_info'].rss / (1024 * 1024), 2) if info['memory_info'] else 0
            processes.append({
                "pid": info['pid'],
                "name": info['name'],
                "cpu_percent": info['cpu_percent'] or 0.0,
                "memory_mb": mem_mb
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    # Sort by memory descending
    processes.sort(key=lambda x: x['memory_mb'], reverse=True)
    return processes[:100] # Return top 100 to avoid freezing UI

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
