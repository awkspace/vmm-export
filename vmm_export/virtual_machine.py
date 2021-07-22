#!/usr/bin/env python3

import asyncio


class VirtualMachine():
    update_futures = []

    def __init__(self, raw_info):
        self.data = raw_info

    def __getattr__(self, name):
        if name in self.data:
            return self.data[name]
        raise AttributeError(name)

    def wait_for_update(self):
        future = asyncio.Future()
        VirtualMachine.update_futures.append(future)
        return future

    def update(self, raw_info):
        self.data = raw_info

    async def wait_for_status(self, status):
        while True:
            await self.wait_for_update()
            if self.status == status:
                return
