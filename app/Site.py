from flask import Flask, render_template, request, redirect, url_for
import pickle
import os

app = Flask(__name__)

# File to store the list of sites
SITES_FILE = "sites.txt"


def load_sites():
    """Load sites from the file."""
    if not os.path.exists(SITES_FILE):
        return []
    with open(SITES_FILE, "rb") as file:
        return pickle.load(file)


def save_sites(sites):
    """Save sites to the file."""
    with open(SITES_FILE, "wb") as file:
        pickle.dump(sites, file)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        site = request.form.get("site")
        if site:
            sites = load_sites()
            if site not in sites:
                sites.append(site)
                save_sites(sites)
        return redirect(url_for("index"))

    sites = load_sites()
    return render_template("index.html", sites=sites)


@app.route("/remove/<site>")
def remove(site):
    sites = load_sites()
    if site in sites:
        sites.remove(site)
        save_sites(sites)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
