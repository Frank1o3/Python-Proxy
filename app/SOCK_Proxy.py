from json import load, JSONDecodeError
from urllib.parse import urlparse
from LRU import LRUCache
import netifaces as ni
import logging
import socket
import os

# Load configuration
CONFIG = "app/Config.json"
if not os.path.exists(CONFIG):
    CONFIG = CONFIG.replace("app/", "")

if not os.path.exists(CONFIG):
    raise FileExistsError(f"{CONFIG} file does not exist")

with open(CONFIG, "r") as file:
    try:
        data = load(file)
        MAX_CACHE_SIZE = data["MAX_CACHE_SIZE"]
        CACHE_FILE = data["CACHE_FILE"]
        BLOCKED_SITES = data["BlockSites"]
        CUSTOMDOMAINS = data["CustomDomains"]
    except JSONDecodeError as e:
        raise e

cache = LRUCache(MAX_CACHE_SIZE)
LOGGINGLEVEL = 3


def get_ip_addresses():
    interfaces = ni.interfaces()
    non_loopback_interfaces = [
        interface for interface in interfaces if not interface.startswith("lo")
    ]
    ip_addresses = []
    for interface in non_loopback_interfaces:
        addrs = ni.ifaddresses(interface)
        ipv4_addrs = addrs.get(ni.AF_INET, [])
        ip_addresses.extend(ipv4_addrs)
    return ip_addresses


def log():
    print("")
    logging.info("-" * 55)
    logging.info("Logging Levels 1 - 3")
    logging.info("Level 1: Logs the HTTP request host and its port.")
    logging.info("Level 2: Logs the URL method and version of a request.")
    logging.info("Level 3: Logs the full request.")
    logging.info("Logging Level set to {}".format(LOGGINGLEVEL))
    logging.info("-" * 55)
    print("")
