from json import load, JSONDecodeError
from urllib.parse import urlparse
from LRU import LRUCache
import http.client
import certifi
import asyncio
import logging
import psutil
import socket
import ssl
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


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        request_line = await reader.readuntil(b"\r\n")
        if not request_line:
            return
        method, url, version = request_line.split(b" ", 2)
        if LOGGINGLEVEL == 3:
            logging.info(request_line)
        elif LOGGINGLEVEL >= 2 and LOGGINGLEVEL < 3:
            logging.info(f"Url: {url} Method: {method} Version: {version}")

        headers = {}
        body = b""
        while True:
            line = await reader.readuntil(b"\r\n")
            if line == b"\r\n":
                break
            header = line.decode("utf-8").strip()
            key, value = header.split(":", 1)
            headers[key.strip()] = value.strip()

        content_length = headers.get("Content-Length")
        if content_length:
            body = await reader.readexactly(int(content_length))

        if method == b"CONNECT":
            await handle_connect(reader, writer, url)
        else:
            await handle_http(reader, writer, method, url, version, headers, body)
    except asyncio.IncompleteReadError:
        logging.error("Error handling request: Incomplete request received")
    except Exception as e:
        logging.error(f"Error handling request: {e}")
    finally:
        writer.close()


async def handle_connect(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, url
):
    host, _, port = url.decode("utf-8").rpartition(":")
    port = int(port)
    for domain in CUSTOMDOMAINS:
        logging.info(domain["name"])
        if host.startswith(domain["name"]):
            args = host.removeprefix(domain["name"])
            if domain["to"] == "0.0.0.0":
                localIP = get_ip_addresses()
            else:
                localIP = None
            host = "".join(
                [
                    domain["to"] if domain["to"] != "0.0.0.0" else localIP,
                    args,
                ]
            )
            port = domain["port"]
            break

    if LOGGINGLEVEL >= 1 and LOGGINGLEVEL < 3:
        logging.info(f"Host: {host} Port: {port}")

    for site in BLOCKED_SITES:
        if site in host:
            logging.info(f"Connection to {site} blocked.")
            writer.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
            await writer.drain()
            writer.close()
            return
    try:
        target_reader, target_writer = await asyncio.open_connection(host, port)
        writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
        await writer.drain()
        await asyncio.gather(
            relay(reader, target_writer),
            relay(target_reader, writer),
        )
    except OSError as e:
        logging.error(f"Error handling CONNECT request: {e}")
    finally:
        writer.close()


async def handle_http(
    reader, writer: asyncio.StreamWriter, method, url, version, headers, body
):
    parsed_url = urlparse(url.decode("utf-8"))
    host = parsed_url.netloc.split(":")[0]
    port = (
        parsed_url.port
        if parsed_url.port
        else 443 if parsed_url.scheme == "https" else 80
    )

    for domain in CUSTOMDOMAINS:
        logging.info(domain["name"])
        if host.startswith(domain["name"]):
            args = host.removeprefix(domain["name"])
            if domain["to"] == "0.0.0.0":
                localIP = get_ip_addresses()
            else:
                localIP = None
            host = "".join(
                [
                    domain["to"] if domain["to"] != "0.0.0.0" else localIP,
                    args,
                ]
            )
            port = domain["port"]
            break

    if LOGGINGLEVEL >= 1 and LOGGINGLEVEL < 3:
        logging.info(f"Host: {host} Port: {port}")

    for site in BLOCKED_SITES:
        if site in host:
            logging.info(f"Connection to {site} blocked.")
            writer.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
            await writer.drain()
            writer.close()
            return

    try:
        # Check if URL is in cache
        cached_data = cache.get(url)

        if cached_data is not None:
            # Make a request to fetch the current data
            if parsed_url.scheme == "https":
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_verify_locations(cafile=certifi.where())
                conn = http.client.HTTPSConnection(host, port, context=context)
            else:
                conn = http.client.HTTPConnection(host, port)

            path = parsed_url.path or "/"
            if parsed_url.query:
                path += "?" + parsed_url.query

            conn.request(method.decode("utf-8"), path, body, headers)
            response = conn.getresponse()
            new_data = response.read()

            # Compare the new data with the cached data
            if new_data == cached_data:
                logging.info(f"Cache hit for {url.decode('utf-8')}")
                writer.write(cached_data)
                await writer.drain()
                return
            else:
                logging.info(f"Cache update for {url.decode('utf-8')}")
                cache.replace(url, new_data)
                writer.write(new_data)
                await writer.drain()
                return

        # If not in cache, make HTTP request and cache the result
        if parsed_url.scheme == "https":
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_verify_locations(cafile=certifi.where())
            conn = http.client.HTTPSConnection(host, port, context=context)
        else:
            conn = http.client.HTTPConnection(host, port)

        path = parsed_url.path or "/"
        if parsed_url.query:
            path += "?" + parsed_url.query

        conn.request(method.decode("utf-8"), path, body, headers)
        response = conn.getresponse()
        data = response.read()

        # Add retrieved data to cache
        cache.add(url, data)
        cache.evict_if_needed()

        writer.write(data)
        await writer.drain()

    except Exception as e:
        logging.error(f"Error handling HTTP request: {e}")

        if cached_data is not None:
            logging.info(
                f"Returning cached data for {url.decode('utf-8')} due to error."
            )
            writer.write(cached_data)
            await writer.drain()
        else:
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            await writer.drain()

    finally:
        writer.close()


async def relay(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            if LOGGINGLEVEL >= 4:
                print("INFO - ", data)
            writer.write(data)
            await writer.drain()
    except asyncio.CancelledError:
        logging.info("Relay task cancelled.")
    except ConnectionResetError:
        logging.info("Connection reset by peer.")
    except Exception as e:
        logging.error(f"Error relaying data: {e}")
    finally:
        writer.close()


def get_ip_addresses():
    interfaces = psutil.net_if_addrs()
    ethernet_ip = None
    wireless_ip = None

    for interface_name, interface_addresses in interfaces.items():
        for address in interface_addresses:
            if address.family == socket.AF_INET:
                if "eth" in interface_name.lower() or "en" in interface_name.lower():
                    ethernet_ip = address.address
                elif "wlan" in interface_name.lower() or "wl" in interface_name.lower():
                    wireless_ip = address.address
    if ethernet_ip:
        return ethernet_ip
    elif wireless_ip:
        return wireless_ip
    else:
        return "127.0.0.1"


def find_available_port(start_port=8080, end_port=65535):
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except socket.error:
                continue
    raise RuntimeError("No available port found")


def get_server_address():
    server_ip = os.environ.get("IP")
    server_port = int(os.environ.get("PORT", 80))
    if server_ip is None or server_ip == "0.0.0.0":
        server_ip = get_ip_addresses()
    if server_port is None or server_port == 80:
        server_port = find_available_port()
    return server_ip, server_port


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


async def main():
    global LOGGINGLEVEL
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    server_ip, server_port = get_server_address()
    LOGGINGLEVEL = 3
    log()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    server = await asyncio.start_server(handle_client, server_ip, server_port)
    async with server:
        logging.info(f"Serving at port {server_port} on IP {server_ip}")
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Server shutdown gracefully.")
    except Exception as e:
        logging.error(f"Server encountered an error: {e}")
