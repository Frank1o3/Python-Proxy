# Proxy Server Application

This project is a Python-based proxy server application designed to handle HTTP requests and responses, potentially for routing or security purposes. It utilizes the `http.client` module for making HTTP requests and the `certifi` package for managing SSL certificates. The application may be containerized using Docker, and it uses a virtual environment for Python dependencies.

## Features

- Handling HTTP requests and responses.
- SSL certificate management with `certifi`.
- Docker containerization for easy deployment.
- Caching mechanism to store HTTP responses.
- Interface and IP address detection for network configuration.

## Requirements

- Python 3.12.3 or higher.
- Docker (optional, for containerization).

## Dependencies

The project requires the following Python packages:

- `certifi`

These dependencies are listed in the `requirements.txt` file.

## Install and use the Proxy
To to this link [INSTALL.md](https://github.com/Frank1o3/Python-Proxy/blob/main/INSTALL.md)

## Usage

Once the application is running, it will start listening for HTTP requests on the specified IP and port. The application logs information about incoming requests and responses, as well as details about the network interfaces it detects.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to report bugs or request new features.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
