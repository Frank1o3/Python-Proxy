# Setup Instructions for Windows (without Docker support)

1. **Clone the repository**: Clone this repository to your local machine.

2. **Install dependencies**: Navigate to the project directory and run the following command to install the required
Python packages:
```bash
    pip install -r requirements.txt
```

3. **Run the application**:
- **Directly**: To run the application directly using Python, follow these steps:
1. Ensure you have Python 3.12.3 or higher installed on your system.
2. Navigate to the project directory in your terminal.
3. If you're using a virtual environment (which is recommended), activate it. If you haven't created a virtual
environment yet, you can do so by running:
```bash
    python -m venv venv
```
And then activate it with:
```bash
    .\venv\Scripts\activate
```
4. Install the required dependencies by running:
```bash
    pip install -r requirements.txt
```
5. Start the application by running:
```bash
    python app/main.py
```