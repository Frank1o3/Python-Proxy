from json import load, JSONDecodeError
import os

CONFIG: str = "app/Config.json"

if not os.path.exists(CONFIG):
    CONFIG = CONFIG.replace("app/", "")


with open(CONFIG, "r") as file:
    try:
        data = load(file)
        MAX_CACHE_SIZE: int = data["MAX_CACHE_SIZE"]
        CACHE_FILE: str = data["CACHE_FILE"]
        BLOCKED_SITES: list[str] = data["BlockSites"]
        CUSTOMDOMAINS: list[dict[str,str,int]]= data["CustomDomains"]
    except JSONDecodeError as e:
        raise e
    finally:
        file.close()
