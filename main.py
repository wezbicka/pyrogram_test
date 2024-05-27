import asyncio

import nest_asyncio

from app.__main__ import main

nest_asyncio.apply()

asyncio.run(main())
