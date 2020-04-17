class BwData:

    def __init__(self, data):
        self.total_rate_in = data["TotalIn"]
        self.rate_im = data["RateIn"]
        self.total_rate_out = data["TotalOut"]
        self.rate_out = data["RateOut"]

    def toJson(self):
        data = {
            "TotalIn": self.total_rate_in,
            "RateIn": self.rate_im,
            "TotalOut": self.total_rate_out,
            "RateOut": self.rate_out
        }
        return data


class BwStats:

    def __init__(self):
        self.bw_data_collection = {}

    def add(self, timestamp, data):
        self.bw_data_collection.update({timestamp: BwData(data)})

    def toJson(self):
        jsonData = {}
        [jsonData.update({str(key): self.bw_data_collection.get(key).toJson()}) for key in
         self.bw_data_collection.keys()]

        return jsonData
