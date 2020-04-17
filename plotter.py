from datetime import datetime
import json
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any


class UpTime:

    def __init__(self):
        self.ledger = {}

    def add(self, id, peer):
        up_periods = []
        for period in peer["up_periods"]:
            up_periods.append(
                (datetime.fromtimestamp(period["to"]) - datetime.fromtimestamp(period["from"])).total_seconds())
        if len(up_periods) > 0:
            avg = np.sum(up_periods) / len(up_periods)
            self.ledger.update({id: avg})

    def getDataForPlot(self):
        data = {
            "<15 min": 0,
            "15 m - 1h": 0,
            "1h - 5h": 0,
            "5h - 10h": 0,
            "> 10h": 0
        }
        for key in self.ledger.keys():
            value = self.ledger[key]
            if value < 900:
                new_value = data.get("<15 min")
                new_value += 1
                data.update({"<15 min": new_value})
            elif value < 3600:
                new_value = data.get("15 m - 1h")
                new_value += 1
                data.update({"15 m - 1h": new_value})
            elif value < 18000:
                new_value = data.get("1h - 5h")
                new_value += 1
                data.update({"1h - 5h": new_value})
            elif value < 36000:
                new_value = data.get("5h - 10h")
                new_value += 1
                data.update({"5h - 10h": new_value})
            else:
                new_value = data.get("> 10h")
                new_value += 1
                data.update({"> 10h": new_value})
        avgs = []
        ranges = data.keys()
        [avgs.append(data.get(key)) for key in ranges]
        return (ranges, avgs)

    def getAvg(self, id):
        return self.ledger.get(id)


class PropertyDistribution:

    def __init__(self):
        self.ledger = {}

    def addOne(self, entity):
        last_amount = self.ledger.get(entity)
        if not last_amount:
            last_amount = 0
        last_amount += 1
        self.ledger.update({entity: last_amount})

    def getDataForPlot(self):
        entities = []
        data = []
        for key in self.ledger.keys():
            entities.append(key)
            data.append(self.ledger[key])
        return (entities, data)


class LatencyXLocation:

    def __init__(self):
        self.ledger = {}

    def addOne(self, country_name, latency):
        latencies = self.ledger.get(country_name)
        if not latencies:
            latencies = []
        latencies.append(latency)
        self.ledger.update({country_name: latencies})

    def getDataForPlot(self):
        countries = []
        latencies = []
        for key in self.ledger.keys():
            countries.append(key)
            latencies.append(np.average(self.ledger[key]))

        return countries, latencies

class HourlyAvgNumberOfPeers:

    def __init__(self):
        self.ledger = {}

    def add(self, timestamp, value):
        dt = datetime.fromtimestamp(float(timestamp))
        hour = dt.hour
        date = str(dt.date())
        if date not in self.ledger.keys():
            dict_hours = {}
            dict_date = {date : dict_hours}
        else:
            dict_date = {date : self.ledger[date]}
            dict_hours = self.ledger[date]

        if hour not in dict_hours.keys():
            dict_hours.update({hour : [value]})
        else:
            dict_hours[hour].append(value)

        dict_date.update({date : dict_hours})

        self.ledger.update(dict_date)


    def get_data_for_plot(self):

        day = {}

        for date in self.ledger.keys():
            for hour in self.ledger[date].keys():
                number_of_peers = np.average(self.ledger[date][hour])
                if hour not in day.keys():
                    day_hour = { hour : [number_of_peers]}
                    day.update(day_hour)
                else:
                    day[hour].append(number_of_peers)


        avg_list = []
        for hour in sorted(day.keys()):
            avg_list.append(np.average(day[hour]))

        return day.keys(), avg_list


class Plotter:

    def __init__(self):
        with open('data/bw_data_file.json') as f:
            self.bw_data = json.load(f)
        with open('data/storage_data_file.json') as f:
            self.storage_data = json.load(f)
        with open('data/number_of_peers_file.json') as f:
            self.number_of_peers = json.load(f)
        with open('data/swarm_data_file.json') as f:
            self.swarm_data = json.load(f)
        self.peers_per_country = PropertyDistribution()
        self.prot_distribution = PropertyDistribution()
        self.up_time = UpTime()
        self.latency_per_country = LatencyXLocation()
        self.hour_avg_peers = HourlyAvgNumberOfPeers()

    def getCsv(self):
        data = ["id,address,nation,region,city,last_seen\n"]
        for key in self.swarm_data.keys():
            peer = self.swarm_data.get(key)
            latencies = peer["latency"]
            valid_latencies = len(latencies)
            total = 0
            for value in latencies:
                l = value["value"]
                if not l == "n/a":
                    if l.find("ms") != -1:
                        total += float(l.split("ms")[0])
                    else:
                        total += float(l.split("s")[0]) * 1000
                else:
                    valid_latencies -= 1
            if valid_latencies > 0:
                latency = total / valid_latencies

            self.up_time.add(key, self.swarm_data.get(key))
            up_time = self.up_time.getAvg(key)
            csv = "{},{},{},{},{},{},{},{}\n".format(key, peer["address"],
                                                     peer["location"]["nation"], peer["location"]["region"],
                                                     peer["location"]["city"],
                                                     peer["last_seen"], latency, up_time)
            data.append(csv)

        csv_file = open("data/swarm_data.csv", "a+")
        [csv_file.write(row) for row in data]

    def number_of_peer(self):
        peers = []
        timestamps = []
        for key in self.number_of_peers.keys():
            peers.append(self.number_of_peers.get(key))
            timestamps.append(datetime.fromtimestamp(float(key)))

        avg = np.average(peers)
        plt.plot(range(len(peers)), peers, 'b', range(len(peers)), [avg] * len(peers), 'g')
        plt.title("Variation of number of peers")
        plt.legend(["Number of peers", "Average number of peers"])
        plt.xlabel("Number of monitor")
        plt.ylabel("Number of peers")
        # plt.xticks(rotation=90)
        plt.savefig("fig/number_of_peer.png",bbox_inches='tight')
        plt.show()

    def peers_location(self):
        for id in self.swarm_data.keys():
            country = self.swarm_data.get(id)["location"]["nation"]
            if not country:
                country = "Not Available"
            self.peers_per_country.addOne(country)

        data = self.peers_per_country.getDataForPlot()
        country_fst_half = data[0][:len(data[0]) // 2]
        country_scd_half = data[0][len(data[0]) // 2:]
        peers_fst_half = data[1][:len(data[1]) // 2]
        peers_scd_half = data[1][len(data[1]) // 2:]
        plt.bar(country_fst_half, peers_fst_half)
        plt.xticks(rotation=90)
        plt.title("Peers distribution part 1")
        plt.xlabel("Countries")
        plt.ylabel("Number of peers")
        fig = plt.gcf()
        fig.set_size_inches(8, 6)
        plt.savefig("fig/peers_location_1.png",bbox_inches='tight')
        plt.show()
        plt.bar(country_scd_half, peers_scd_half)
        plt.xticks(rotation=90)
        plt.title("Peers distribution part 2")
        plt.xlabel("Countries")
        plt.ylabel("Number of peers")
        fig = plt.gcf()
        fig.set_size_inches(8, 6)
        plt.savefig("fig/peers_location_2.png",bbox_inches='tight')
        plt.show()

    def up_time_peers(self):
        for id in self.swarm_data.keys():
            self.up_time.add(id, self.swarm_data.get(id))

        data = self.up_time.getDataForPlot()
        plt.bar(data[0], data[1])
        plt.xticks(rotation=90)
        plt.title("Up time peers")
        plt.xlabel("Up time")
        plt.ylabel("Number of peers")
        plt.savefig("fig/up_time_peers.png",bbox_inches='tight')
        plt.show()

    def incoming_bandwidth_consumption(self):
        data = []
        for key in self.bw_data.keys():
            data.append(self.bw_data.get(key)["RateIn"])
        indexes = np.arange(0, len(data), 1)

        avg = np.average(data)
        avgs = [avg] * len(data)

        plt.plot(indexes, data, 'b', indexes, avgs, 'g')
        plt.title("Incoming bandwidth consumption")
        plt.legend(["Bandwidth 'In-Rate'", "Average 'In-Rate'"])
        plt.xlabel("Number of monitor")
        plt.ylabel("Bandwidth consumption (bits)")
        # plt.xticks(rotation=90)
        plt.savefig("fig/incoming_bandwidth_consumption.png",bbox_inches='tight')
        plt.show()

    def outgoing_bandwidth_consumption(self):
        data = []
        for key in self.bw_data.keys():
            data.append(self.bw_data.get(key)["RateOut"])
        indexes = np.arange(0, len(data), 1)

        avg = np.average(data)
        avgs = [avg] * len(data)

        plt.plot(indexes, data, 'b', indexes, avgs, 'g')
        plt.title("Outgoing bandwidth consumption")
        plt.legend(["Bandwidth 'Out-Rate'", "Average 'Out-Rate'"])
        plt.xlabel("Number of monitor")
        plt.ylabel("Bandwidth consumption (bits)")
        # plt.xticks(rotation=90)
        plt.savefig("fig/outgoing_bandwidth_consumption.png",bbox_inches='tight')
        plt.show()

    def stored_blocks_amount(self):
        data = []
        for key in self.storage_data.keys():
            data.append(self.storage_data.get(key)["NumObjects"])
        indexes = np.arange(0, len(data), 1)

        plt.plot(indexes, data, 'b')
        plt.title("Variation of the stored blocks")
        plt.legend(["Blocks variation"])
        plt.xlabel("Number of monitor")
        plt.ylabel("Number of blocks")
        # plt.xticks(rotation=90)
        plt.savefig("fig/stored_blocks_amount.png",bbox_inches='tight')
        plt.show()


    def latency_get_file(self):
        pass

    def avg_latency(self):
        pass

    def protocol_distribution(self):
        for id in self.swarm_data.keys():
            address = self.swarm_data.get(id)["address"]
            address_components = address.split("/")
            protocol = "{}/{}".format(address_components[1], address_components[3])
            self.prot_distribution.addOne(protocol)

        data = self.prot_distribution.getDataForPlot()
        plt.bar(data[0], data[1])
        plt.xticks(rotation=90)
        plt.title("Protocol distribution")
        plt.xlabel("Protocol")
        plt.ylabel("Number of peers")
        plt.savefig("fig/protocol_distribution.png",bbox_inches='tight')
        plt.show()

    def avg_latency_per_location(self):
        for id in self.swarm_data.keys():
            latency_raw_values = self.swarm_data.get(id)["latency"]
            country = self.swarm_data.get(id)["location"]["nation"]
            if not country:
                country = "Not Available"

            if len(latency_raw_values) > 0:
                latencies = []
                for value in latency_raw_values:
                    raw_latency = value.get("value")
                    if raw_latency == "n/a":
                        pass
                    elif raw_latency.find("ms") > 0:
                        latencies.append(float(raw_latency.split("ms")[0]))
                    else:
                        latencies.append(1000 * float(raw_latency.split("s")[0]))
            else:
                latencies = [0]

            if len(latencies) > 0:
                self.latency_per_country.addOne(country, np.average(latencies))

        data = self.latency_per_country.getDataForPlot()
        plt.bar(data[0], data[1])
        plt.xticks(rotation=90)
        plt.title("Average latency per country")
        plt.xlabel("Country")
        plt.ylabel("Average latency")
        fig = plt.gcf()
        fig.set_size_inches(10, 6)
        plt.savefig("fig/avg_latency_per_location.png", bbox_inches='tight')
        plt.show()

    def hourly_avg_number_of_peers(self):
        for key in self.number_of_peers.keys():
            self.hour_avg_peers.add(key, self.number_of_peers.get(key))

        data = self.hour_avg_peers.get_data_for_plot()
        plt.bar(data[0], data[1])
        plt.xticks(rotation=90)
        plt.title("Average number of peers per hour of the day")
        plt.xlabel("Hour of the day")
        plt.ylabel("Number of peers")
        fig = plt.gcf()
        fig.set_size_inches(10, 6)
        plt.savefig("fig/hour_avg_peers.png", bbox_inches='tight')
        plt.show()



if __name__ == "__main__":
    plotter = Plotter()
    plotter.hourly_avg_number_of_peers()
    plotter.number_of_peer()
    plotter.peers_location()
    plotter.up_time_peers()
    plotter.incoming_bandwidth_consumption()
    plotter.outgoing_bandwidth_consumption()
    plotter.stored_blocks_amount()
    plotter.latency_get_file()
    plotter.avg_latency()
    plotter.protocol_distribution()
    plotter.avg_latency_per_location()
    # plotter.getCsv()
