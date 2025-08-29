""" Main Script """

import asyncio
from proxy import Proxy

if __name__ == '__main__':
    proxy = Proxy()
    asyncio.run(proxy.main())
