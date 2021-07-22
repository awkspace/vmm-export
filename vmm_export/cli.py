#!/usr/bin/env python3

import aiohttp
import asyncio
import configargparse
import json
from vmm_export import logger
from vmm_export.virtual_machine import VirtualMachine


def main():
    asyncio.run(run())


async def run():
    opts = parse_args()
    logger.setLevel(opts.log_level)
    url = f'http://{opts.dsm_url}'

    async with aiohttp.ClientSession() as session:
        sid = await dsm_login(session, url, opts.username, opts.password)

        exclude_list = opts.exclude.split(',')
        include_list = opts.include.split(',')
        vms = await get_vms(session, url, sid, exclude_list, include_list)
        vm_info_task = asyncio.create_task(
            check_vm_info(session, url, sid, vms))

        queue = asyncio.Queue()
        for vm in vms:
            queue.put_nowait({
                'session': session,
                'url': url,
                'sid': sid,
                'vm': vm,
                'path': opts.path
            })

        tasks = []
        for _ in range(int(opts.workers)):
            task = asyncio.create_task(worker(queue))
            tasks.append(task)

        await queue.join()

        for task in tasks:
            task.cancel()

        vm_info_task.cancel()


async def worker(queue):
    while True:
        job = await queue.get()
        await export_vm(**job)
        queue.task_done()


async def dsm_login(session, url, username, password):
    async with session.get(
            f'{url}/webapi/auth.cgi',
            params={
                'api': 'SYNO.API.Auth',
                'version': '3',
                'method': 'login',
                'account': username,
                'passwd': password,
                'format': 'sid',
                'session': 'vmm_export'
            }
    ) as raw_response:
        r = await raw_response.json(content_type=None)
        raise_for_success(r)
        return r['data']['sid']


async def get_vms(session, url, sid, exclude_list, include_list):
    vm_info = await list_vms(session, url, sid)
    vms = []
    for vm_data in vm_info:
        if include_list and vm_data['guest_name'] in include_list:
            vms.append(VirtualMachine(vm_data))
        elif vm_data['guest_name'] not in exclude_list:
            vms.append(VirtualMachine(vm_data))
    return vms


async def check_vm_info(session, url, sid, vms):
    while True:
        await asyncio.sleep(5)
        if VirtualMachine.update_futures:
            await update_vm_info(session, url, sid, vms)


async def list_vms(session, url, sid):
    async with session.get(
            f'{url}/webapi/entry.cgi',
            params={
                '_sid': sid,
                'api': 'SYNO.Virtualization.API.Guest',
                'method': 'list',
                'version': '1'
            }
    ) as raw_response:
        r = await raw_response.json(content_type=None)
        raise_for_success(r)
        return r['data']['guests']


async def update_vm_info(session, url, sid, vms):
    vm_info = await list_vms(session, url, sid)
    for vm_data in vm_info:
        for vm in vms:
            if vm.guest_id == vm_data['guest_id']:
                vm.update(vm_data)
    for future in VirtualMachine.update_futures:
        future.set_result(None)
    VirtualMachine.update_futures = []


async def power_off_vm(session, url, sid, vm):
    async with session.get(
            f'{url}/webapi/entry.cgi',
            params={
                '_sid': sid,
                'api': 'SYNO.Virtualization.API.Guest.Action',
                'version': '1',
                'method': 'poweroff',
                'guest_name': vm.guest_name
            }
    ) as raw_response:
        r = await raw_response.json(content_type=None)
        raise_for_success(r)


async def power_on_vm(session, url, sid, vm):
    # Guests being exported are still in 'shutdown' status, so there is no
    # status to wait for. Instead, the most consistent way to wait until they
    # can start up again is to spam the poweron command until we no longer
    # receive an error, or we receive an error telling us the VM is already on.
    while True:
        try:
            async with session.get(
                    f'{url}/webapi/entry.cgi',
                    params={
                        '_sid': sid,
                        'api': 'SYNO.Virtualization.API.Guest.Action',
                        'version': '1',
                        'method': 'poweron',
                        'guest_name': vm.guest_name
                    },
                    timeout=60
            ) as raw_response:
                r = await raw_response.json(content_type=None)
                if r['success']:
                    break
                elif r['error']['code'] == 904:  # Machine is already running
                    break
                await asyncio.sleep(60)
        except asyncio.TimeoutError:
            pass


async def start_vm_export(session, url, sid, vm, path):
    async with session.get(
        f'{url}/webapi/entry.cgi',
        params={
            '_sid': sid,
            'api': 'SYNO.Virtualization.Guest.Action',
            'version': '1',
            'method': 'export',
            'target_ova_path': path,
            'ova_mode': '0',
            'guest_id': vm.guest_id,
            'name': vm.guest_name
        }
    ) as raw_response:
        r = await raw_response.json(content_type=None)
        raise_for_success(r)


async def delete_old_export(session, url, sid, vm, path):
    async with session.get(
            f'{url}/webapi/entry.cgi',
            params={
                '_sid': sid,
                'api': 'SYNO.FileStation.Delete',
                'version': '2',
                'method': 'delete',
                'path': f'{path}/{vm.guest_name}.ova'
            }
    ) as raw_response:
        r = await raw_response.json(content_type=None)
        raise_for_success(r)


async def export_vm(session, url, sid, vm, path):
    initial_status = vm.status

    await delete_old_export(session, url, sid, vm, path)
    await power_off_vm(session, url, sid, vm)
    await vm.wait_for_status('shutdown')
    await start_vm_export(session, url, sid, vm, path)

    if initial_status != 'running':
        return  # Don't restart a VM that wasn't running

    await power_on_vm(session, url, sid, vm)
    await vm.wait_for_status('running')


def raise_for_success(response):
    if not response['success']:
        logger.error(f'Error from DSM: {json.dumps(response)}')
        raise RuntimeError('Error from DSM')


def parse_args():
    p = configargparse.ArgParser(auto_env_var_prefix='VME_')
    p.add('-c', '--config', required=False, is_config_file=True,
          help='Path to configuration file.')
    p.add('--username', required=True,
          help='Username to use for logging into the DSM.')
    p.add('--password', required=True,
          help='Password to use for logging into the DSM.')
    p.add('--dsm-url', required=True,
          help='URL of the DSM, including port, e.g. 192.168.1.100:5000.')
    p.add('--path', required=True,
          help='The path to export VMs to, e.g. /MyShareName/VMM.')
    p.add('--workers', required=False, default='1',
          help='How many VMs should be exported in parallel.')
    p.add('--exclude', required=False, default='',
          help='Comma-separated list of VM names to exclude from exporting.')
    p.add('--include', required=False, default='',
          help='Comma-separated list of VM names to include in exporting. '
          'Takes precedence over --exclude.')
    p.add('--log-level', required=False, default='WARNING',
          help='Log verbosity.')
    return p.parse_args()
