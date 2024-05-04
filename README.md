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
- `netifaces`

These dependencies are listed in the `requirements.txt` file.

## Setup

1. **Clone the repository**: Clone this repository to your local machine.

2. **Install dependencies**: Navigate to the project directory and run the following command to install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Build Docker image**: If you wish to containerize the application using Docker, build the Docker image by running:

   ```bash
   docker build -t proxy-server .
   ```

   This command builds a Docker image named `proxy-server` using the `Dockerfile` provided in the project. The Docker setup includes creating and using a virtual environment for Python dependencies.

4. **Run the application**:

   - **Directly**: To run the application directly using Python, follow these steps:

     1. Ensure you have Python 3.12.3 or higher installed on your system.
     2. Navigate to the project directory in your terminal.
     3. If you're using a virtual environment (which is recommended), activate it. If you haven't created a virtual environment yet, you can do so by running:

        ```bash
        python -m venv venv
        ```

        And then activate it with:

        - On Windows:

          ```bash
          .\venv\Scripts\activate
          ```

        - On macOS and Linux:

          ```bash
          source venv/bin/activate
          ```

     4. Install the required dependencies by running:

        ```bash
        pip install -r requirements.txt
        ```

     5. Start the application by running:

        ```bash
        python app/main.py
        ```

        This will start the proxy server application, and it will begin listening for HTTP requests on the specified IP and port.

   - **Using Docker**: To run the application in a Docker container, follow these steps:

     1. Ensure Docker is installed and running on your system.
     2. Navigate to the project directory in your terminal.
     3. Build the Docker image (if you haven't already) by running:

        ```bash
        docker build -t proxy-server .
        ```

     4. Run the Docker container with the following command:

        ```bash
        docker run -p 8080:8080 proxy-server
        ```

        This command maps port 8080 of the container to port 8080 of the host machine, allowing you to access the proxy server application through your web browser or any HTTP client by navigating to `http://localhost:8080` or using the appropriate IP address if you're running the container on a different host.

## Usage

Once the application is running, it will start listening for HTTP requests on the specified IP and port. The application logs information about incoming requests and responses, as well as details about the network interfaces it detects.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to report bugs or request new features.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
