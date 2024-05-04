# Proxy Server Application

This project is a Python-based proxy server application designed to handle HTTP requests and responses, potentially for routing or security purposes. It utilizes the `aiohttp` library for asynchronous HTTP requests and the `certifi` package for managing SSL certificates. The application may be containerized using Docker.

## Features

- Asynchronous HTTP request handling using `aiohttp`.
- SSL certificate management with `certifi`.
- Docker containerization for easy deployment.
- Caching mechanism to store HTTP responses.
- Interface and IP address detection for network configuration.

## Requirements

- Python 3.12.3 or higher.
- Docker (optional, for containerization).

## Dependencies

The project requires the following Python packages:

- `aiohttp`
- `certifi`
- `netifaces`

These dependencies are listed in the `requirements.txt` file.

## Setup

1. **Clone the repository**: Clone this repository to your local machine.

2. **Install dependencies**: Navigate to the project directory and run the following command to install the required Python packages:
   bash pip install -r requirements.txt

3. **(Optional) Build Docker image**: If you wish to containerize the application using Docker, build the Docker image by running:

bash docker build -t proxy-server .

This command builds a Docker image named `proxy-server` using the `Dockerfile` provided in the project.

4.  **Run the application**:

    - **Directly**: Run the application directly using Python:

           ```

      bash python app/main.py

    - **Using Docker**: If you've built the Docker image, you can run the application in a Docker container:

           ```

      bash docker run -p 8080:8080 proxy-server

           This command runs the `proxy-server` Docker image, mapping port 8080 of the container to port 8080 of the host machine.

## Usage

Once the application is running, it will start listening for HTTP requests on the specified IP and port. The application logs information about incoming requests and responses, as well as details about the network interfaces it detects.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to report bugs or request new features.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
