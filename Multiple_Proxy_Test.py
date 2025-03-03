import multiprocessing
import asyncio
import signal
import logging
import time
from Proxy import Proxy
from typing import List

processes: List[multiprocessing.Process] = []


def run_proxy(port: int):
    """Start a proxy instance with a specific port."""
    proxy = Proxy(PORT=port)
    try:
        asyncio.run(proxy.Start())
    except asyncio.CancelledError:
        logging.info(f"Proxy on port {port} received shutdown signal.")
    finally:
        logging.info(f"Proxy on port {port} has stopped.")


def shutdown_proxies(signum, frame):
    """Gracefully stop all proxies when exiting."""
    logging.info("Shutdown signal received. Stopping all proxies...")
    for p in processes:
        if p.is_alive():
            logging.info(f"Terminating proxy process {p.name}")
            p.terminate()  # Send termination signal
    for p in processes:
        p.join()  # Ensure all proxies close properly
    logging.info("All proxies stopped. Exiting.")
    exit(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")

    num_cores = multiprocessing.cpu_count()
    num_proxies = max(1, num_cores - 1)  # Reserve 1 core for the OS

    logging.info(f"Starting {num_proxies} proxy instances.")

    # Register signal handlers
    # Handle keyboard interrupt (Ctrl+C)
    signal.signal(signal.SIGINT, shutdown_proxies)
    # Handle termination signal
    signal.signal(signal.SIGTERM, shutdown_proxies)

    # Start proxies with unique ports
    start_port = 19132  # Choose a base port
    for i in range(num_proxies):
        port = start_port + i  # Increment port for each proxy
        p = multiprocessing.Process(target=run_proxy, args=(port,))
        p.start()
        processes.append(p)

    # Keep main process running to catch signals
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Catch keyboard interrupt and gracefully shut down proxies
        logging.info("Caught KeyboardInterrupt. Initiating shutdown.")
        shutdown_proxies(None, None)
