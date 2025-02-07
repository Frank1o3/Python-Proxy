from collections import OrderedDict


class LFUCache:
    def __init__(self, max_size):
        self.cache = OrderedDict()  # Store the cache
        self.access_count = {}  # Track how many times each key was accessed
        self.max_size = max_size

    def add(self, key, value):
        if key in self.cache:
            del self.cache[key]  # Refresh position in OrderedDict
        self.cache[key] = value
        self.access_count[key] = 0  # Initialize access count for the new entry
        self.evict_if_needed()

    def get(self, key):
        if key in self.cache:
            # Increment the access count each time an item is accessed
            self.access_count[key] += 1
            return self.cache[key]
        return None

    def evict_if_needed(self):
        while len(self.cache) > self.max_size:
            # Evict the least-frequently used item
            least_frequent_key = min(self.access_count, key=self.access_count.get)
            del self.cache[least_frequent_key]
            del self.access_count[least_frequent_key]

    def replace(self, key, value):
        if key in self.cache:
            self.cache[key] = value
            self.access_count[key] = 0  # Reset access count after replacement
        self.evict_if_needed()
