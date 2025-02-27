""" Import's """

from asyncio import StreamReader, StreamWriter, open_connection, gather
from json import load, JSONDecodeError
from collections import OrderedDict
from urllib.parse import urlparse
import http.client as http
import certifi
import psutil
import socket
import ssl


class LRFUCache:
    def __init__(self, lru_capacity=50, lfu_capacity=50) -> None:
        self.lru_cache = OrderedDict()
        self.lfu_cache = OrderedDict()
        self.lru_capacity = lru_capacity
        self.lfu_capacity = lfu_capacity
        self.access_count = {}

    # TODO make the esential cache data etc


class Proxy:
    def __init__(self, IP="0.0.0.0", PORT=8080) -> None:
        self.PORT = PORT
        self.IP = IP
