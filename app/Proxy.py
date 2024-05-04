from flask import Flask, render_template, request, redirect, url_for, jsonify
from collections import defaultdict
from urllib.parse import urlparse
import http.client
import threading
import asyncio
import logging
import certifi
import pickle
import math
import time
import ssl
import os

# Cache dictionary to store HTTP responses
cache = {}
request_frequency = defaultdict(int)

# Maximum size of the cache
MAX_CACHE_SIZE = 25

# Cache file path
CACHE_FILE = "cache.pkl"
SITES_FILE = "sites.pkl"

# Initialize an empty set for blocked sites
blocked_sites = list()

# Flask app initialization
app = Flask(__name__)


def load_sites():
    """Load sites from the file."""
    if not os.path.exists(SITES_FILE):
        return set()
    with open(SITES_FILE, "rb") as file:
        return pickle.load(file)


def save_sites(sites):
    """Save sites to the file."""
    with open(SITES_FILE, "wb") as file:
        pickle.dump(sites, file)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        site = request.form.get("site")
        if site:
            if site not in blocked_sites:
                blocked_sites.add(site)
                save_sites(blocked_sites)
        return redirect(url_for("index"))

    return render_template("index.html", sites=blocked_sites)


@app.route("/remove/<site>")
def remove(site):
    if site in blocked_sites:
        blocked_sites.remove(site)
        save_sites(blocked_sites)
    return redirect(url_for("index"))


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        request = await reader.readuntil(b"\r\n\r\n")
        if not request:
            return
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


async def handle_http(reader, writer: asyncio.StreamWriter, method, url, version):
    global cache, blocked_sites, request_frequency
    parsed_url = urlparse(url.decode("utf-8"))
    host = parsed_url.netloc.split(":")[0]
    port = (
        parsed_url.port
        if parsed_url.port
        else 443 if parsed_url.scheme == "https" else 80
    )

    try:
        # Check if the requested URL is in the list of blocked sites
        if host in blocked_sites:
            # Return a custom HTML response indicating that the site is blocked
            response = b"HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n"
            response += b"<html><body><h1>403 Forbidden</h1><p>This site is blocked.</p></body></html>"
            writer.write(response)
            await writer.drain()
            return

        # If the host is a local address, forward the request to the local Flask server
        if host == "10.0.0.50" or host == "localhost":
            # Connect to the local Flask server
            local_reader, local_writer = await asyncio.open_connection(
                "127.0.0.1", int(os.environ.get("SITE_PORT", 8080))
            )

            # Forward the original request to the local server
            local_writer.write(request.encode())
            await local_writer.drain()

            # Relay data between the client and the local server
            await asyncio.gather(
                relay(reader, local_writer),
                relay(local_reader, writer),
            )

            return

        # Perform the HTTP request to the external server
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
    server_ip = os.environ.get("SERVER_IP", "0.0.0.0")
    server_port = int(os.environ.get("SERVER_PORT", 8080))
    return server_ip, server_port


async def start_proxy_server():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    server_ip, server_port = get_server_address()

    server = await asyncio.start_server(handle_client, server_ip, server_port)
    async with server:
        logging.info(f"Serving at port {server_port} on IP {server_ip}")
        await server.serve_forever()


def run_flask_app():
    site_ip = os.environ.get("SITE_IP", "0.0.0.0")
    site_port = int(os.environ.get("SITE_PORT", 8080))
    app.run(host=site_ip, port=site_port, debug=True, use_reloader=False)


if __name__ == "__main__":
    blocked_sites = load_sites()
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    # Run proxy server in the main thread
    try:
        loop.run_until_complete(start_proxy_server())
    finally:
        loop.close()
