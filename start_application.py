import os
import sys
import json
import subprocess

own_host = subprocess.run(["hostname", "-I", "|", "awk", "'{print $1}'"], capture_output=True)
def start_application():
    config = json.load(open("config.json"))
    host1, host2, host3 = config["host1"], config["host2"], config["host3"]
    os.system("systemctl start memcached")
    #os.system("systemctl start rqlite")
    node_id = 1 if own_host == host1 else (2 if own_host == host2 else 3)
    print(own_host)
    if own_host == host1:
        os.system(f"bash -c \"pushd /home/pi/rqlite; nohup /home/pi/rqlite/rqlited -node-id 1 "
                  f"-http-addr={own_host}:4001 "
                  f"-raft-addr={own_host}:4002 "
                  f"data & disown; popd\"")
    else:
        os.system(f"bash -c \"pushd /home/pi/rqlite; nohup /home/pi/rqlite/rqlited -node-id {node_id} "
                  f"-http-addr={own_host}:4001 "
                  f"-raft-addr={own_host}:4002 "
                  f"-join {host1}:4002 data & disown; popd\"")
