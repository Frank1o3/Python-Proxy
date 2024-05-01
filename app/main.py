import ssl
import pickle
import asyncio
import logging
import certifi
import http.client
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Cache dictionary to store HTTP responses
cache = {}
request_count = 0


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    global request_count, cache

    try:
        request = await reader.readuntil(b"\r\n\r\n")

        if not request:
            return

        request_line = request.split(b"\r\n")[0]
        method, url, version = request_line.split(b" ", 2)
        logging.info(request)
        if method == b"CONNECT":
            await handle_connect(reader, writer, url)
        else:
            await handle_http(reader, writer, method, url, version)

        request_count += 1
        if request_count % 100 == 0:
            logging.info("Clearing cache")
            cache.clear()
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
    except Exception as e:
        logging.error(f"Error handling CONNECT request: {e}")
    finally:
        writer.close()


async def handle_http(reader: asyncio.StreamReader, writer, method, url, version):
    global cache

    parsed_url = urlparse(url.decode("utf-8"))
    host = parsed_url.netloc.split(":")[0]
    port = (
        parsed_url.port
        if parsed_url.port
        else 443 if parsed_url.scheme == "https" else 80
    )

    try:
        if url in cache:
            logging.info(f"Cache hit for {url.decode('utf-8')}")
            writer.write(cache[url])
            await writer.drain()
            return

        if parsed_url.scheme == "https":
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_verify_locations(cafile=certifi.where())
            conn = http.client.HTTPSConnection(host, port, context=context)
        else:
            conn = http.client.HTTPConnection(host, port)

        conn.request(method.decode("utf-8"), parsed_url.path)
        response = conn.getresponse()
        data = response.read()

        cache[url] = data

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
        # Handle cancellation gracefully
        logging.info("Relay task cancelled.")
    except ConnectionResetError:
        # Connection reset by peer
        logging.info("Connection reset by peer.")
    except Exception as e:
        logging.error(f"Error relaying data: {e}")
    finally:
        writer.close()


async def main():
    server_ip = "10.0.0.31"  # Use your server's IP address
    port = 8080  # Choose a port for your proxy server

    server = await asyncio.start_server(handle_client, server_ip, port)

    async with server:
        logging.info(f"Serving at port {port} on IP {server_ip}")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
