import socket


def find_available_port(start_port=8080, end_port=65535):
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except socket.error:
                continue
    raise RuntimeError("No available port found")


if __name__ == "__main__":
    available_port = find_available_port()
    print(f"Available Port: {available_port}")
