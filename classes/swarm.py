import os
import time
import ipinfo
from dotenv import load_dotenv
from main import fromUnicode

ip_processed = {}


class Peer:

    def __init__(self, peer, timestamp=time.time()):
        self.id = fromUnicode(peer["Peer"])
        self.last_address = fromUnicode(peer["Addr"])
        self.location = find_state(fromUnicode(peer["Addr"]))
        self.latencies = [fromUnicode(peer["Latency"])]
        self.up_from = timestamp
        self.last_seen = timestamp
        self.alive = True
        self.up_periods = []  # [{"from": time, "to": time}]

    def update(self, timestamp, latency):
        if not self.alive:
            self.alive = True
            self.up_from = timestamp

        self.last_seen = timestamp
        self.latencies.append(latency)
        return self

    def checkpoint(self, timestamp):
        self.last_seen = timestamp

    def gone_down(self):
        if self.alive:
            self.alive = False
            self.up_periods.append({"from": self.up_from, "to": self.last_seen})
            self.up_from = ""

    def toJson(self):
        latency = []
        [latency.append({"value": value.decode('utf-8')}) for value in self.latencies]
        data = {
            self.id.decode("utf-8"): {
                "address": self.last_address.decode('utf-8'),
                "location": {
                    "nation": self.location["country_name"],
                    "region": self.location["region"],
                    "city": self.location["city"]
                },
                "last_seen": self.last_seen,
                "up_periods": self.up_periods,
                "latency": latency
            }}

        return data


class Swarm:

    def __init__(self):
        self.peers = {}

    def add(self, peer, timestamp):
        current = fromUnicode(peer["Peer"])
        latency = fromUnicode(peer["Latency"])
        if current not in self.peers:
            newPeer = Peer(peer, timestamp)
        else:
            newPeer = self.peers.get(current).update(timestamp, latency)

        self.peers.update({current: newPeer})

    def kill_nodes(self, gone_nodes):
        [self.peers.get(x).gone_down() for x in gone_nodes]

    def toJson(self):
        data = {}
        [data.update(self.peers.get(key).toJson()) for key in self.peers.keys()]

        return data



def find_state(ip):
    if ip in ip_processed:
        return ip_processed.get(ip)

    load_dotenv()
    access_token = os.getenv('ACCESS_TOKEN')
    handler = ipinfo.getHandler(access_token)
    try:
        data = handler.getDetails(ip.decode("utf-8").split("/")[2])
        ip_data = {
            "country_name": data.country_name,
            "region": data.region,
            "city": data.city
        }
    except Exception:
        ip_data = {
            "country_name": None,
            "region": None,
            "city": None
        }

    ip_processed.update({ip: ip_data})
    return ip_data
