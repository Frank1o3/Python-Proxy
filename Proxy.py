""" Import's """

from asyncio import StreamReader, StreamWriter, CancelledError, IncompleteReadError, open_connection, start_server, gather, run
from json import load, dump, JSONDecodeError
from collections import OrderedDict
from urllib.parse import urlparse
from typing import Dict, Optional
import http.client as http
import logging
import certifi
import psutil
import socket
import ssl
import os


class LRFUCache:
    def __init__(self, lru_capacity=50, lfu_capacity=50, cache_file="cache.json") -> None:
        self.lru_cache = OrderedDict()
        self.lfu_cache = OrderedDict()
        self.lru_capacity = lru_capacity
        self.lfu_capacity = lfu_capacity
        self.access_count = {}
        self.cache_file = cache_file
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as file:
                    data = load(file)
                    self.lru_cache = OrderedDict(data.get("lru_cache", {}))
                    self.lfu_cache = OrderedDict(data.get("lfu_cache", {}))
                    self.access_count = data.get("access_count", {})
            except JSONDecodeError:
                logging.warning("Cache file is corrupted. Resetting cache.")
                self._save_cache()

    def _save_cache(self):
        with open(self.cache_file, "w", encoding="utf-8") as file:
            dump({"lru_cache": self.lru_cache, "lfu_cache": self.lfu_cache,
                 "access_count": self.access_count}, file)

    def get(self, key: str) -> Optional[bytes]:
        if key in self.lru_cache:
            self.lru_cache.move_to_end(key)
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.lru_cache[key]
        if key in self.lfu_cache:
            self.access_count[key] += 1
            return self.lfu_cache[key]
        return None

    def put(self, key: str, value: bytes):
        if key in self.lru_cache or key in self.lfu_cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
        else:
            self.access_count[key] = 1

        if len(self.lru_cache) < self.lru_capacity:
            self.lru_cache[key] = value
        elif len(self.lfu_cache) < self.lfu_capacity:
            self.lfu_cache[key] = value
        else:
            least_accessed = min(
                self.access_count, key=lambda k: self.access_count[k])
            if least_accessed in self.lfu_cache:
                del self.lfu_cache[least_accessed]
            elif least_accessed in self.lru_cache:
                del self.lru_cache[least_accessed]
            del self.access_count[least_accessed]
            self.lru_cache[key] = value

        self._save_cache()


class Proxy:
    def __init__(self, IP="0.0.0.0", PORT=8080) -> None:
        self.PORT = PORT
        self.IP = IP
        try:
            with open("Config.json", "r", encoding="utf-8") as file:
                self.data = load(file)  # Load JSON file content
        except JSONDecodeError:
            raise RuntimeError("Was not able to load JSON file: Config.json")
        except FileNotFoundError as e:
            logging.error(e)

        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        with open("site/block.html", "r", encoding="utf-8") as file:
            self.html_file = file.read().encode()
            file.close()

        self.cache = LRFUCache(
            self.data["Max_Cache_Size"], self.data["Max_Cache_Size"], self.data["Cache_File"])

    async def __handle_client(self, reader: StreamReader, writer: StreamWriter) -> None:
        """ Handle Client's"""
        try:
            request_line = await reader.readuntil(b"\r\n")
            if not request_line:
                return
            method, url, _ = request_line.split(b" ", 2)
            headers = {}
            body = bytes()

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

            if method.lower() == b"connect":
                await self.__handle_connect(reader, writer, url)
            else:
                logging.info(request_line)
                await self.__handle_http(writer, method, url, headers, body)
        except IncompleteReadError as e:
            logging.error(e)
        finally:
            writer.close()

    async def __handle_connect(self, reader: StreamReader, writer: StreamWriter, url: bytes) -> None:
        """Handle Connection's"""
        parsed_url = urlparse(url.decode("utf-8"))
        host, _, port = url.decode("utf-8").rpartition(":")
        port = (
            int(port) if port.isnumeric(
            ) else 443 if parsed_url.scheme == "https" else 80
        )

        try:
            if self.__Should_Block(host) or host == "/" or not host:
                writer.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
                await writer.drain()
                writer.close()
                return

            target_reader, target_writer = await open_connection(host=host, port=port)
            writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            await writer.drain()
            await gather(
                self.__relay(reader, target_writer),
                self.__relay(target_reader, writer)
            )
        except ConnectionAbortedError as e:
            logging.error(e)
        except ConnectionRefusedError as e:
            logging.error(e)
        except socket.gaierror as e:
            logging.error(e)
        finally:
            writer.close()

    async def __handle_http(self, writer: StreamWriter, method: bytes, url: bytes, headers: Dict[str, str], body: bytes) -> None:
        """Handle Http Communication"""
        parsed_url = urlparse(url.decode("utf-8"))
        host, _, port = url.decode("utf-8").rpartition(":")
        port = (
            int(port) if port.isnumeric(
            ) else 443 if parsed_url.scheme == "https" else 80
        )
        cache_key = f"{method.decode()}:{parsed_url.geturl()}"

        try:
            if self.__Should_Block(host) or host == "/" or not host:
                writer.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
                await writer.drain()
                writer.close()
                return

            cached_response = self.cache.get(cache_key)
            if cached_response:
                writer.write(cached_response)
                await writer.drain()
                return

            if parsed_url.scheme.lower() == "https":
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_verify_locations(cafile=certifi.where())
                conn = http.HTTPSConnection(
                    host=host, port=port, context=context
                )
            else:
                conn = http.HTTPConnection(host=host, port=port)

            path = parsed_url.path or "/"
            if parsed_url.query:
                path += f"?{parsed_url.query}"

            conn.request(method=method.decode("utf-8"),
                         url=path, body=body, headers=headers)

            response = conn.getresponse()
            data = response.read()

            response_headers = f"HTTP/1.1 {response.status} {response.reason}\r\n".encode()
            for key, value in response.getheaders():
                response_headers += f"{key}: {value}\r\n".encode()

            response_headers += b"\r\n"
            full_response = response_headers + data
            self.cache.put(cache_key, full_response)

            writer.write(full_response)
            await writer.drain()
        except ConnectionAbortedError as e:
            logging.error(e)
        except ConnectionRefusedError as e:
            logging.error(e)
        except socket.gaierror as e:
            logging.error(e)
        finally:
            writer.close()

    async def __relay(self, reader: StreamReader, writer: StreamWriter) -> None:
        """Handle Relaying Data"""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except CancelledError:
            logging.error("Relay task cancelled.")
        except ConnectionResetError:
            logging.error("Connection reset by peer.")
        finally:
            writer.close()

    def __Should_Block(self, host: str) -> bool:
        """If the site getting accessed should be block"""
        for site in self.data["BlockedSites"]:
            if str(site).lower() in host.lower():
                return True
        return False

    async def __get_ip(self) -> None:
        """Get the first available Ethernet or Wireless IP address."""
        interfaces = psutil.net_if_addrs()
        ethernet_ips = []
        wireless_ips = []

        for interface_name, interface_addresses in interfaces.items():
            for address in interface_addresses:
                if address.family == socket.AF_INET:
                    if "eth" in interface_name.lower() or "en" in interface_name.lower():
                        ethernet_ips.append(address.address)
                    elif "wlan" in interface_name.lower() or "wl" in interface_name.lower():
                        wireless_ips.append(address.address)

        self.IP = ethernet_ips[0] if ethernet_ips else (
            wireless_ips[0] if wireless_ips else "127.0.0.1")

    async def __find_available_port(self, start_port=19132, end_port=65535, fallback_port=8080) -> None:
        """Find an available port within the given range, with a fallback."""
        for port in range(start_port, end_port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    # Bind immediately to lock the port
                    s.bind(("0.0.0.0", port))
                    # Ensure the port is usable for TCP connections
                    s.listen(1)
                    s.close()  # Close so the actual proxy server can use it
                    self.PORT = port
                    logging.info(f"Found available port: {self.PORT}")
                    return  # Exit early once a free port is found
                except OSError:
                    continue  # Port is in use, try the next one
        logging.warning(
            f"No available port found in range {start_port}-{end_port}, falling back to {fallback_port}")
        self.PORT = fallback_port  # Fallback only if no port was found

    async def Start(self) -> None:
        """Start the server"""

        if self.IP == "0.0.0.0":
            await self.__get_ip()

        if self.PORT == 8080:
            await self.__find_available_port()

        try:
            server = await start_server(
                self.__handle_client,
                host=self.IP, port=self.PORT
            )
            async with server:
                logging.info(f"Serving at port {self.IP} on IP {self.PORT}")
                await server.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down server....")


if __name__ == "__main__":
    server = Proxy()
    run(server.Start())
