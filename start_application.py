import os
import sys
import json
import time
import atexit


def start_application():
    """
    Startet die Anwendung auf dem Host, der in der Konfigurationsdatei angegeben ist.
    :return:
    """
    config = json.load(open("config.json"))
    own_hostnames = os.popen("hostname -I").read().strip().split(" ")
    own_host = None
    host1, host2, host3 = config["host1"], config["host2"], config["host3"]
    # Hostname des aktuellen Hosts ermitteln
    for own_hostname in own_hostnames:
        if own_hostname in (host1, host2, host3):
            own_host = own_hostname
            break
    if own_host is None:
        sys.exit("This host is not in the config file. Please change the config file to include this host.")

    node_id = 1 if own_host == host1 else (2 if own_host == host2 else 3)
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
    # Warte bis rqlite gestartet ist. Führt sonst zu Fehlern.
    for i in range(10):
        if os.system("curl -s http://localhost:4001/status") == 0:
            break
        time.sleep(1)
    db_pid = os.popen("pgrep rqlited").read().strip()
    if db_pid:
        # Beende rqlite, wenn das Programm beendet wird.
        atexit.register(lambda: os.system(f"kill -9 {db_pid}"))
    else:
        sys.exit("Failed to start rqlite")
    return own_host