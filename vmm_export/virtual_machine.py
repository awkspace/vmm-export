#!/usr/bin/env python3

import asyncio
from vmm_export.cli import dsm_request


class VirtualMachine():
    update_futures = []

    def __init__(self, raw_info):
        self.data = raw_info
        self.export_task = None
        self.export_task_id = None
        self.export_finished = False

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

    async def wait_for_export(self):
        while True:
            await self.wait_for_update()
            if self.export_finished:
                return

    async def update_export_task(self, session, url, sid):
        if not self.export_task_id:
            return
        r = await dsm_request(
            session,
            f'{url}/webapi/entry.cgi',
            params={
                '_sid': sid,
                'api': 'SYNO.Virtualization.API.Task.Info',
                'version': '1',
                'method': 'get',
                'task_id': self.export_task_id
            }
        )
        if r['data']['finish']:
            self.export_task_id = None
            self.export_finished = True
        self.export_task = r
