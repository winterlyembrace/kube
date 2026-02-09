#!/usr/bin/python3

import uuid
import time
from datetime import datetime, timezone

try:

    string = str(uuid.uuid4())

    while True:

        now = datetime.now(timezone.utc)
        timestamp = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        print(f"{timestamp}: {string}")

        time.sleep(5)

    done

except(KeyboardInterrupt):

    print(f"\nStopped")

