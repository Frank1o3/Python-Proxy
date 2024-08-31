import psutil
import socket


def get_primary_ip():
    interfaces = psutil.net_if_addrs()

    ethernet_ip = None
    wireless_ip = None

    for interface_name, interface_addresses in interfaces.items():
        for address in interface_addresses:
            if address.family == socket.AF_INET:
                if "eth" in interface_name.lower() or "en" in interface_name.lower():
                    ethernet_ip = address.address
                elif "wlan" in interface_name.lower() or "wl" in interface_name.lower():
                    wireless_ip = address.address

    if ethernet_ip:
        return ethernet_ip
    elif wireless_ip:
        return wireless_ip
    else:
        return "127.0.0.1"


if __name__ == "__main__":
    primary_ip = get_primary_ip()
    print(f"Primary IP Address: {primary_ip}")
