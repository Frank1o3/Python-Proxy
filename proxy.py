"""Proxy Implementation with LRFU Cache Support"""

from http.client import HTTPConnection, HTTPSConnection
from urllib.parse import urlparse, ParseResult
from typing import Dict, Tuple
import socket
import asyncio
import ssl
import signal
import logging
import uvloop
import certifi

from cache import LRFUCache

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


class Proxy:
    """Proxy Implementation"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8443, buffer_size: int = 4096) -> None:
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.stop_event = asyncio.Event()
        self.cache = LRFUCache()

    async def __handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming client request"""
        try:
            initial = await reader.readline()
            method, url, version = initial.decode("utf-8").strip().split(" ")
            headers = {}
            body = b""

            while True:
                line = await reader.readline()
                if line == b"\r\n":
                    break
                header = line.decode("utf-8").strip()
                if ":" in header:
                    key, value = header.split(":", 1)
                    headers[key.strip()] = value.strip()

            content_len = headers.get("Content-Length")
            if content_len:
                body = await reader.readexactly(int(content_len))

            if method.upper() == "CONNECT":
                host, port = url.split(":", 1)
                writer.write(
                    f"{version} 200 Connection established\r\n\r\n".encode())
                await writer.drain()
                await self.__handle_connect(reader, writer, (host, int(port)))
            else:
                parsed = urlparse(url)
                await self.__handle_http(parsed, method, headers, body, writer, version)

        except asyncio.IncompleteReadError:
            logging.warning("[-] Incomplete read")
        except (ValueError, IndexError, UnicodeDecodeError, OSError) as e:
            logging.exception("[!] Error in __handle_client: %s", e)
        finally:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()

    async def __handle_connect(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, target: Tuple[str, int]):
        """Handle HTTPS CONNECT tunnel"""
        host, port = target
        try:
            logging.info("[+] CONNECT to %s:%s", host, port)
            target_reader, target_writer = await asyncio.open_connection(host=host, port=port, family=socket.AF_INET)
            await writer.drain()

            await asyncio.gather(
                self.__relay(reader, target_writer),
                self.__relay(target_reader, writer)
            )
        except (OSError, asyncio.TimeoutError, ConnectionError) as e:
            logging.error("[!] CONNECT error to %s:%s - %s", host, port, e)

    async def __relay(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Relay data between client and target"""
        try:
            while not reader.at_eof() and not self.stop_event.is_set():
                data = await reader.read(self.buffer_size)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionResetError, OSError) as e:
            logging.error("[!] Relay error: %s", e)
        finally:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()

    async def __handle_http(self, data: ParseResult, method: str, headers: Dict[str, str], body: bytes, writer: asyncio.StreamWriter, version: str):
        """Handle regular HTTP(S) request"""
        try:
            full_url = data.geturl()
            host = data.hostname
            port = data.port or (443 if data.scheme == "https" else 80)

            if not host:
                writer.write(
                    f"{version} 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n".encode())
                await writer.drain()
                logging.warning("[!] No host found in URL")
                return

            path = data.path or "/"
            if data.query:
                path += f"?{data.query}"

            logging.info("[+] HTTP %s %s://%s:%s%s", method,
                         data.scheme, host, port, path)

            cached = self.cache.get(method, full_url, headers, body)
            if cached:
                logging.debug("[+] Serving from cache")
                writer.write(cached)
                await writer.drain()
                return

            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_verify_locations(cafile=certifi.where())

            conn = HTTPSConnection(
                host, port, context=context) if data.scheme == "https" else HTTPConnection(host, port)
            conn.request(method, path, body=body, headers=headers)
            response = conn.getresponse()
            content = response.read()

            response_headers = f"{version} {response.status} {response.reason}\r\n"
            for key, value in response.getheaders():
                clean_value = value.replace("\r", "").replace("\n", "")
                response_headers += f"{key}: {clean_value}\r\n"
            response_headers += "\r\n"

            full_response = response_headers.encode() + content
            self.cache.set(method, full_url, headers, body, full_response)

            writer.write(full_response)
            await writer.drain()

        except (ssl.SSLError, socket.error, ConnectionError, TimeoutError, OSError, ValueError) as e:
            logging.error("[!] HTTP error for %s %s to %s:%s - %s", method,
                          data.geturl(), data.hostname, data.port or 'default', e)

            await writer.drain()

    async def main(self):
        """Run Proxy"""
        server = await asyncio.start_server(self.__handle_client, self.host, self.port)
        addr = f"{self.host}:{self.port}"
        logging.info("[+] Listening on %s", addr)

        loop = asyncio.get_running_loop()

        def shutdown():
            logging.warning("[!] Received shutdown signal")
            self.stop_event.set()

        loop.add_signal_handler(signal.SIGINT, shutdown)
        loop.add_signal_handler(signal.SIGTERM, shutdown)

        async with server:
            await self.stop_event.wait()
            server.close()
            await server.wait_closed()


if __name__ == "__main__":
    proxy = Proxy()
    asyncio.run(proxy.main())
