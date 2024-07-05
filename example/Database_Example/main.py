from flask import Flask, render_template
import netifaces as ni


def get_ip_addresses():
    interfaces = ni.interfaces()
    non_loopback_interfaces = [
        interface for interface in interfaces if not interface.startswith("lo")
    ]
    ip_addresses = []
    for interface in non_loopback_interfaces:
        addrs = ni.ifaddresses(interface)
        ipv4_addrs = addrs.get(ni.AF_INET, [])
        ip_addresses.extend(ipv4_addrs)
    return ip_addresses


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


if __name__ == "__main__":
    ip = get_ip_addresses()[0]["addr"]
    app.run(host=ip, port=3000, debug=False)
