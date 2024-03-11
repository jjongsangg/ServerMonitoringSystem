import psutil
from flask import Flask
import json
import os
import threading
from flask_cors import CORS
from time import sleep

app = Flask(__name__)
CORS(app)

def byte_transform(bytes, to, bsize=1024):
    a = {'k' : 1, 'm': 2, 'g' : 3, 't' : 4, 'p' : 5, 'e' : 6 }
    r = float(bytes)
    for i in range(a[to]):
        r = r / bsize
    return round(r,2)

net_recv_bps = 0
net_sent_bps = 0
prev_net_recv = 0
prev_net_sent = 0

def cal_net_kbps():
    global net_recv_bps, net_sent_bps, prev_net_recv, prev_net_sent
    while True:
        net_recv = psutil.net_io_counters().bytes_recv
        net_sent = psutil.net_io_counters().bytes_sent

        net_recv_bps = net_recv - prev_net_recv
        net_sent_bps = net_sent - prev_net_sent

        prev_net_recv = net_recv
        prev_net_sent = net_sent
        sleep(1)

thread_cal_net = threading.Thread(target=cal_net_kbps)
thread_cal_net.start()

@app.route('/')
def index():
    global net_recv_bps, net_sent_bps
    # CPU 정보 얻기
    cpu_percent = os.popen("top -bn1 | grep \"Cpu(s)\" | awk '{printf(\"%.1f\", 100 - $8)}'").read()
    cpu_count = psutil.cpu_count()

    # 메모리 정보 얻기
    virtual_memory = psutil.virtual_memory()

    total_memory = virtual_memory.total // (1024*1024)
    available_memory = virtual_memory.available // (1024*1024)
    used_memory = total_memory - available_memory

    # 디스크 정보 얻기
    disk_usage = psutil.disk_usage('/')

    total_disk_space = disk_usage.total // (1024*1024*1024)
    used_disk_space = disk_usage.used // (1024*1024*1024)


    hdd_temp = os.popen("sudo smartctl -A /dev/sda | grep Temperature_Celsius | awk '{print $10}'").read()
    cpu_temp = os.popen("vcgencmd measure_temp").read()
    cpu_temp = cpu_temp.split("=")[1].replace("'C","")

    tmp = {
       # "units" : {
       #     "disk" : "GB",
       #     "mem" : "MB"
       # },
        "values" : {
            "total_disk" : total_disk_space,
            "used_disk" : used_disk_space,
            "cpu_per" : cpu_percent,
            "cpu_cores" : cpu_count,
            "total_mem" : total_memory,
            "used_mem" : used_memory,
            "hdd_temp" : hdd_temp.strip(),
            "cpu_temp" : cpu_temp.strip(),
            "net_recv_kbps" : f"{byte_transform(net_recv_bps,'k')}",
            "net_sent_kbps" : f"{byte_transform(net_sent_bps,'k')}",
        }
    }
    return json.dumps(tmp)

if __name__ == '__main__':  
    app.run("0.0.0.0", port=9999)
