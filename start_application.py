import os
import sys
import json


def start_application():
    config = json.load(open("config.json"))
    host1, host2, host3 = config["host1"], config["host2"], config["host3"]
    os.system("systemctl start memcached")
    os.system(f"pushd /home/pi/rqlite && nohup /home/pi/rqlite/rqlited -node-id $(hostname -I | awk '{{print $1}}') "
              f"-http-addr=$(hostname -I | awk '{{print $1}}'):4001 "
              f"-raft-addr=$(hostname -I | awk '{{print $1}}'):4002 "
              f"-bootstrap-expect 3 -join {host1}:4002,{host2}:4002,{host3}:4002 data & disown && popd")
