import json
import argparse
import time
import requests
import unicodedata
import classes


def fromUnicode(data):
    return unicodedata.normalize('NFKD', data).encode('ascii', 'ignore')


class Monitor:

    def __init__(self, hour, frequency):
        self.swarm = classes.Swarm()
        self.bw_stats = classes.BwStats()
        self.storage_stats = classes.StorageStats()
        self.peer_number = {}
        self.current = current = 0
        self.hour = hour
        self.frequency = frequency

    def run(self, data_path):
        while self.current < self.hour:

            rPeer = requests.get("http://localhost:5001/api/v0/swarm/peers?latency=true")
            rBW = requests.get("http://localhost:5001/api/v0/stats/bw")
            bandwidth = rBW.json()
            rStorage = requests.get("http://localhost:5001/api/v0/repo/stat")
            storage = rStorage.json()

            timestamp = time.time()

            if rPeer.status_code == 200:
                peers = rPeer.json()

                added_peers = []
                for peer in peers["Peers"]:
                    self.swarm.add(peer, timestamp)
                    added_peers.append(str(peer["Peer"]).encode("utf-8"))

                peers_to_kill = list(set(self.swarm.peers.keys()) - set(added_peers))
                self.swarm.kill_nodes(peers_to_kill)

                self.peer_number.update({str(timestamp): len(added_peers)})

            if rBW.status_code == 200:
                self.bw_stats.add(timestamp, bandwidth)

            if rStorage.status_code == 200:
                self.storage_stats.add(timestamp, storage)

            self.save(data_path)

            time.sleep(self.frequency)

            self.current += 1

        [self.swarm.peers.get(key).gone_down() for key in self.swarm.peers.keys()]

    def save(self, path):
        data = self.swarm.toJson()
        with open("{}/swarm_data_file.json".format(path), "w+") as f:
            f.write(json.dumps(self.swarm.toJson()))
        with open("{}/bw_data_file.json".format(path), "w+") as f:
            f.write(json.dumps(self.bw_stats.toJson()))
        with open("{}/storage_data_file.json".format(path), "w+") as f:
            f.write(json.dumps(self.storage_stats.toJson()))
        with open("{}/number_of_peers_file.json".format(path), "w+") as f:
            f.write(json.dumps(self.peer_number))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Run IPFS monitoring')
    parser.add_argument('--data_path', type=str,
                        help='path of mocked data_original csv', required=True)
    parser.add_argument('--duration', type=str,
                        help='path of mocked video', required=True)
    parser.add_argument('--frequency', type=str,
                        help='path of mocked video', required=True)

    args = parser.parse_args()

    monitor = Monitor(int(args.duration), float(args.frequency))
    monitor.run(args.data_path)