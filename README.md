# Übersicht für das Programm
## 1. Installation
Das Programm ist zum Zeitpunkt der Abgabe auf allen drei RaspberryPis installiert. Diese Anweisung ist nur für den Fall dass es erneut installiert werden muss
### 1.1 Memcached installieren
Die installation von memcached ist sehr simpel, muss aber auf jedem gerät dass Teil des Clusters sein soll ausgeführt werden:
```bash
sudo apt install memcached libmemcached-tools -y
```
Danach folgendes config file im Repository in /etc/memcached.conf verwenden.

### 1.2 RQLite Installieren
Dafür muss zunächst die Binary unter https://github.com/rqlite/rqlite/releases heruntergeladen werden. Für den RaspberryPi muss die Linux-Arm64 version verwendet werden.
Am praktischten ist hierfür der wget befehl.
Danach entpacken und umbenennen:
```bash
tar -xzvf <dateiname>.tar.gz
mv <Ordnername> rqlite
```

### 1.3 Programm installieren
Dafür einfach dieses Git-Repo in /home/pi/studienprojekte/ Klonen. 
Danach alle notwendigen Python-Pakete installieren. 
(Optional) Virtuelle Umgebung
```bash
python -m venv venv
source ./venv/bin/activate
```
Pakete:
```bash
pip install -r requirements.txt
```

## 2. Programm Konfigurieren
In config.json sind die relevanten Konfigurationen für das Programm. An erster Stelle stehen die IP-Adressen mit Port, für alle Memcached-Knoten, danach der Port für RQLite, 
danaach kommen alle Hosts die zu Beginn im Cluster sein sollen und als letztes der Port,
auf dem die Applikation gehostet wird. Das Programm wird selbst herausfinden welcher Host es von den angegebenen Hosts ist.

Zusätzlich sollte noch die .service-Datei aus dem Repository in /etc/systemd/system abgelegt werden.

## 3. Programm Starten/Stoppen
Das Programm lässt sich mit folgenden Befehlen starten und stoppen:
```bash
#start:
systemctl start distcache.service
#stop
systemctl stop distcache.service
```

## 4. Schnittstellen
Alle Schnittstellen sind bereits im Code beschrieben. Die wichtigsten beiden sind:
http://<IP>:PORT/distcache/image/{id} : Gibt ein Bild zurück. Zufällig generiert; einfarbig.
http://<IP>:PORT/distcache/event : SSE für Bildupdates


