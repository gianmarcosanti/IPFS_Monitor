class StorageData:

    def __init__(self, data):
        self.repo_size = data["RepoSize"]
        self.num_objects = data["NumObjects"]

    def toJson(self):
        data = {
            "RepoSize": self.num_objects,
            "NumObjects": self.repo_size
        }
        return data


class StorageStats:

    def __init__(self):
        self.storage_data_collection = {}

    def add(self, timestamp, data):
        self.storage_data_collection.update({timestamp: StorageData(data)})

    def toJson(self):
        jsonData = {}
        [jsonData.update({str(key): self.storage_data_collection.get(key).toJson()}) for key in
         self.storage_data_collection.keys()]

        return jsonData
