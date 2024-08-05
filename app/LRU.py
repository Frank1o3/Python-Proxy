from collections import OrderedDict


class LRUCache:
    def __init__(self, max_size):
        self.cache = OrderedDict()
        self.max_size = max_size

    def add(self, key, value):
        if key in self.cache:
            del self.cache[key]  # Refresh position in OrderedDict
        self.cache[key] = value
        self.evict_if_needed()

    def get(self, key):
        if key in self.cache:
            # Move accessed item to the end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def evict_if_needed(self):
        while len(self.cache) > self.max_size:
            self.cache.popitem(
                last=False
            )  # Remove the first item (least recently used)

    def replace(self, url, value):
        for key in self.cache:
            if key == url:
                self.cache[key] = value
        self.evict_if_needed()
