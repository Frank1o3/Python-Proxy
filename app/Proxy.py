from json import load, JSONDecodeError
from collections import defaultdict
from urllib.parse import urlparse
import http.client
import asyncio
import logging
import certifi
import pickle
import math
import time
import ssl
import os


# Cache dictionary to store HTTP responses
save = 0
cache = {}
request_frequency = defaultdict(int)

# Cache file path

if os.path.exists("Config.json"):
    with open("Config.json", "r") as file:
        try:
            data = load(file)
            MAX_CACHE_SIZE: int = data["MAX_CACHE_SIZE"]
            CACHE_FILE: str = data["CACHE_FILE"]
            BLOCKED_SITES: list = data["BlockSites"]
            LOGGINGLEVEL: int = data["LoggingLevel"]
        except JSONDecodeError as e:
            raise e
        finally:
            file.close()
else:
    raise Exception("Config.json file does not exists")


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        request = await reader.readuntil(b"\r\n\r\n")
        if not request:
            return
        if LOGGINGLEVEL == 3:
            logging.info(request)
        request_line = request.split(b"\r\n")[0]
        method, url, version = request_line.split(b" ", 2)
        if method == b"CONNECT":
            await handle_connect(reader, writer, url)
        else:
            await handle_http(reader, writer, method, url, version)
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
    for site in BLOCKED_SITES:
        if site in host:
            logging.info(f"Connection to {site} blocked.")
            # Close the writer without sending a response
            writer.close()
            return
    try:
        # Establish a connection to the target server
        target_reader, target_writer = await asyncio.open_connection(host, port)

        # Send a 200 Connection established response to the client
        writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
        await writer.drain()

        # Relay data between the client and the target server
        await asyncio.gather(
            relay(reader, target_writer),
            relay(target_reader, writer),
        )
    except OSError as e:
        logging.error(f"Error handling CONNECT request: {e}")
    finally:
        writer.close()


async def serve_blocked_page(writer: asyncio.StreamWriter):
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Connection: close\r\n"
        "\r\n"
        "<!DOCTYPE html>\r\n"
        "<html>\r\n"
        "<head><title>Access Blocked</title></head>\r\n"
        "<body>\r\n"
        "<h1>Access to this website is blocked.</h1>\r\n"
        "</body>\r\n"
        "</html>\r\n"
    )
    writer.write(response.encode())
    await writer.drain()
    writer.close()


async def handle_http(reader, writer: asyncio.StreamWriter, method, url, version):
    global cache, request_frequency, save, BLOCK_SITE_FILE
    parsed_url = urlparse(url.decode("utf-8"))
    host = parsed_url.netloc.split(":")[0]
    port = (
        parsed_url.port
        if parsed_url.port
        else 443 if parsed_url.scheme == "https" else 80
    )
    if LOGGINGLEVEL > 1:
        logging.info(f"Host: {host} Port: {port}")
    for site in BLOCKED_SITES:
        if site in host:
            logging.info(f"Connection to {site} blocked.")
            # Close the writer without sending a response
            writer.close()
            return
    try:
        if url in cache:
            logging.info(f"Cache hit for {url.decode('utf-8')}")
            writer.write(cache[url])
            await writer.drain()

            # Update request frequency for cached URL
            request_frequency[url] += 1

            logging.info(f"{len(cache)} {math.floor((MAX_CACHE_SIZE / 2))}")

            # Check cache size and evict least used items if needed
            if len(cache) >= math.floor((MAX_CACHE_SIZE / 2)):
                logging.info("evict_cache_items")
                evict_cache_items()
            if (save % MAX_CACHE_SIZE) == 0:
                logging.info("saving cache")
                save_cache()
            return

        # Perform the HTTP request
        if parsed_url.scheme == "https":
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_verify_locations(cafile=certifi.where())
            conn = http.client.HTTPSConnection(host, port, context=context)
        else:
            conn = http.client.HTTPConnection(host, port)

        conn.request(method.decode("utf-8"), parsed_url.path)
        response = conn.getresponse()
        data = response.read()

        # Cache the response
        cache[url] = data
        request_frequency[url] += 1

        logging.info(f"{len(cache)} {math.floor((MAX_CACHE_SIZE / 2))}")

        # Check cache size and evict least used items if needed
        if len(cache) >= math.floor((MAX_CACHE_SIZE / 2)):
            logging.info("evict_cache_items")
            evict_cache_items()
        if (save % MAX_CACHE_SIZE) == 0:
            logging.info("saving cache")
            save_cache()

        writer.write(data)
        await writer.drain()
    except Exception as e:
        logging.error(f"Error handling HTTP request: {e}")
    finally:
        writer.close()


async def relay(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
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


def save_cache():
    global cache

    # Save cache to file
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    time.sleep(0.5)
    with open(CACHE_FILE, "wb") as file:
        pickle.dump(cache, file)


def evict_cache_items():
    global cache, request_frequency

    # Sort cache items by request frequency in descending order
    sorted_items = sorted(request_frequency.items(), key=lambda x: x[1], reverse=True)

    # Remove least used items until cache size is within limits
    while len(cache) > MAX_CACHE_SIZE:
        url, _ = sorted_items.pop()
        logging.info(f"Url: {url} was used: {request_frequency[url]}")
        if request_frequency[url] < 5:
            del request_frequency[url]
            del cache[url]


async def load_cache():
    global cache

    # Load cache from file if it exists
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as file:
            cache = pickle.load(file)


def get_server_address():
    server_ip = os.environ.get("PROXY_IP", "10.0.0.31")
    server_port = int(os.environ.get("PROXY_PORT", 8080))
    return server_ip, server_port


async def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    server_ip, server_port = get_server_address()

    server = await asyncio.start_server(handle_client, server_ip, server_port)
    async with server:
        logging.info(f"Serving at port {server_port} on IP {server_ip}")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
    print("Hi!! :D")
