import socketserver
import socket
import http.client
from urllib.parse import urlparse
import logging
import ssl
import certifi  # Ensure you have certifi installed for CA certificates
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Cache dictionary to store HTTP responses
cache = {}
request_count = 0


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class Proxy(socketserver.BaseRequestHandler):

    def handle(self):
        request_line = self.request.recv(1024).strip()
        if not request_line:
            return
        logging.info(request_line)
        method, url, version = request_line.split(b" ", 2)
        if method == b"CONNECT":
            self.handle_connect(url)
        else:
            self.handle_http(method, url, version)

        # Clear cache after every 100 requests
        global request_count, cache
        if request_count % 100 == 0:
            logging.info("Clearing cache")
            cache.clear()
        request_count += 1

    def handle_connect(self, url):
        host, _, port = url.decode("utf-8").rpartition(":")
        port = int(port)
        try:
            # Create a new socket and establish a connection
            conn = socket.create_connection((host, port))

            # Create an SSL context for client-side operations
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.load_verify_locations(cafile=certifi.where())

            # Wrap the socket with SSL/TLS for client-side operations
            ssl_conn = context.wrap_socket(conn, server_hostname=host)

            # Send a 200 Connection established response to the client
            self.request.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")

            # Relay data between the client and the target server
            self.relay(self.request, ssl_conn)
        except Exception as e:
            logging.error(f"Error handling CONNECT request: {e}")

    def handle_http(self, method, url, version):
        global cache
        # Parse the URL to extract the hostname and port
        parsed_url = urlparse(url.decode("utf-8"))
        host = parsed_url.netloc.split(":")[0]  # Extract the hostname
        port = (
            parsed_url.port
            if parsed_url.port
            else 443 if parsed_url.scheme == "https" else 80
        )  # Extract the port, default to 443 for HTTPS and 80 for HTTP

        try:
            # Check if the response is in the cache
            if url in cache:
                logging.info(f"Cache hit for {url.decode('utf-8')}")
                self.request.sendall(cache[url])
                return

            # Use HTTPSConnection for HTTPS requests
            if parsed_url.scheme == "https":
                # Create an SSL context for client-side operations
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_verify_locations(cafile=certifi.where())
                conn = http.client.HTTPSConnection(host, port, context=context)
            else:
                conn = http.client.HTTPConnection(host, port)

            conn.request(method.decode("utf-8"), parsed_url.path)
            response = conn.getresponse()
            data = response.read()

            # Add the response to the cache
            cache[url] = data

            self.request.sendall(data)
        except Exception as e:
            logging.error(f"Error handling HTTP request: {e}")

    def relay(self, source, destination):
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    logging.info("Connection closed")
                    break
                destination.sendall(data)
        except Exception as e:
            logging.error(f"Error relaying data: {e}")


if __name__ == "__main__":
    server_ip = "10.0.0.31"  # Use your server's IP address
    port = 8080  # Choose a port for your proxy server
    with ThreadedTCPServer((server_ip, port), Proxy) as httpd:
        logging.info(f"Serving at port {port} on IP {server_ip}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("Received KeyboardInterrupt. Shutting down server...")
            httpd.shutdown_request()
            httpd.server_close()