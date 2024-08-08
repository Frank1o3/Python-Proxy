## Setup

1. **Clone the repository**: Clone this repository to your local machine.

2. **Install dependencies**: Navigate to the project directory and run the following command to install the required Python packages:
   bash pip install -r requirements.txt

3. **(Optional) Build Docker image**: If you wish to containerize the application using Docker, build the Docker image by running:

bash docker build -t proxy-server .

This command builds a Docker image named `proxy-server` using the `Dockerfile` provided in the project. The Docker setup includes creating and using a virtual environment for Python dependencies.

4.  **Run the application**:

    - **Directly**: To run the application directly using Python, follow these steps: 1. Ensure you have Python 3.12.3 or higher installed on your system. 2. Navigate to the project directory in your terminal. 3. If you're using a virtual environment (which is recommended), activate it. If you haven't created a virtual environment yet, you can do so by running:

      ````
      bash python -m venv venv

              And then activate it with:
              - On Windows:
                ```

      bash .\venv\Scripts\activate

              - On macOS and Linux:
                ```

      bash source venv/bin/activate

           4. Install the required dependencies by running:
              ```

      bash pip install -r requirements.txt

           5. Start the application by running:
              ```

      bash python app/main.py

      ````

      - **Using Docker**: To run the application in a Docker container, follow these steps: 1. Ensure Docker is installed and running on your system. 2. Navigate to the project directory in your terminal. 3. Build the Docker image (if you haven't already) by running:

      ````
      bash docker build -t python-proxy -f "$(pwd)/DOCKERFILE" .
                ```

      bash docker run -d --restart unless-stopped --network host -e PROXY_IP="0.0.0.0" -e PROXY_PORT=8080 --name python-proxy python-proxy .

                This command runs the container in detached mode
                ```

      docker logs -f python-proxy
              This command will lets you see the docker image logs if you dont want to see the logs press ctrl + c to close or exit
              ```
      ````