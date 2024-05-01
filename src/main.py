import socketserver
import http.client
from urllib.parse import urlparse
import logging
import ssl
import certifi  # Ensure you have certifi installed for CA certificates

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class Proxy(socketserver.BaseRequestHandler):
    def handle(self):
        request_line = self.request.recv(1024).strip()
        if not request_line:
            return
        method, url, version = request_line.split(b" ", 2)
        logging.info(f"Request: {request_line}")
        if method == b"CONNECT":
            self.handle_connect(url)
        else:
            self.handle_http(method, url, version)

    def handle_connect(self, url):
        host, _, port = url.decode("utf-8").rpartition(":")
        port = int(port)
        try:
            # Create a new socket and establish a connection
            conn = socketserver.socket.create_connection((host, port))

            # Create an SSL context for client-side operations
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(
                certfile="rootCA.pem", keyfile="rootCA.key"
            )  # Adjust paths as necessary

            # Wrap the socket with SSL/TLS for client-side operations
            ssl_conn = context.wrap_socket(conn, server_hostname=host)

            # Send a 200 Connection established response to the client
            self.request.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            logging.info(f"CONNECT request handled for {host}:{port}")

            # Relay data between the client and the target server
            self.relay(self.request, ssl_conn)
        except Exception as e:
            logging.error(f"Error handling CONNECT request: {e}")

    def handle_http(self, method, url, version):
        # Parse the URL to extract the hostname and port
        parsed_url = urlparse(url.decode("utf-8"))
        host = parsed_url.netloc.split(":")[0]  # Extract the hostname
        port = (
            parsed_url.port if parsed_url.port else 80
        )  # Extract the port, default to 80 if not specified

        conn = None  # Initialize conn to None before the try block
        try:
            conn = http.client.HTTPConnection(host, port)
            conn.request(method.decode("utf-8"), parsed_url.path)
            response = conn.getresponse()
            self.request.sendall(response.read())
            logging.info(f"HTTP request handled for {url.decode('utf-8')}")
        except Exception as e:
            logging.error(f"Error handling HTTP request: {e}")
        finally:
            if (
                conn is not None
            ):  # Check if conn is defined before attempting to close it
                conn.close()

    def relay(self, source, destination):
        while True:
            data = source.recv(4096)
            if not data:
                logging.info("Connection closed")
                break
            destination.sendall(data)


if __name__ == "__main__":
    server_ip = "10.0.0.31"  # Use your server's IP address
    port = 8081  # Choose a port for your proxy server
    with ThreadedTCPServer((server_ip, port), Proxy) as httpd:
        logging.info(f"Serving at port {port} on IP {server_ip}")
        httpd.serve_forever()
