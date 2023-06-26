#!/usr/bin/env python3

import aiohttp
import asyncio
import configargparse
import json
from vmm_export import logger, dsm_request
from vmm_export.virtual_machine import VirtualMachine
from vmm_export.dsm_errors import dsm_errors


def main():
    asyncio.run(run())


async def run():
    opts = parse_args()
    logger.setLevel(opts.log_level)
    url = f'http://{opts.dsm_url}'
    tasks = []

    async with aiohttp.ClientSession() as session:
        sid = await dsm_login(session, url, opts.username, opts.password)

        exclude_list = opts.exclude.split(',')
        include_list = opts.include.split(',')
        logger.info('Retrieving list of VMs...')
        vms = await get_vms(session, url, sid, exclude_list, include_list)

        task = asyncio.create_task(
            check_vm_info(session, url, sid, vms, opts.path))
        tasks.append(task)

        queue = asyncio.Queue()
        for vm in vms:
            queue.put_nowait({
                'session': session,
                'url': url,
                'sid': sid,
                'vm': vm,
                'path': opts.path
            })

        for _ in range(int(opts.workers)):
            task = asyncio.create_task(worker(queue))
            tasks.append(task)

        await queue.join()

        for task in tasks:
            task.cancel()

    logger.info('Exports completed.')


async def worker(queue):
    while True:
        job = await queue.get()
        await export_vm(**job)
        queue.task_done()


async def dsm_login(session, url, username, password):
    r = await dsm_request(
            session,
            f'{url}/webapi/auth.cgi',
            params={
                'api': 'SYNO.API.Auth',
                'version': '3',
                'method': 'login',
                'account': username,
                'passwd': password,
                'format': 'sid',
                'session': 'dsm_info'
            }
    )
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


async def list_vms(session, url, sid):
    r = await dsm_request(
        session,
        f'{url}/webapi/entry.cgi',
        params={
            '_sid': sid,
            'api': 'SYNO.Virtualization.API.Guest',
            'method': 'list',
            'version': '1'
        }
    )
    return r['data']['guests']


async def check_vm_info(session, url, sid, vms, path):
    while True:
        await asyncio.sleep(5)
        if VirtualMachine.update_futures:
            try:
                await update_vm_info(session, url, sid, vms, path)
            except Exception:
                logger.exception('Error in VM info update task')


async def update_vm_info(session, url, sid, vms, path):
    vm_info = await list_vms(session, url, sid)
    for vm_data in vm_info:
        for vm in vms:
            if vm.guest_id == vm_data['guest_id']:
                vm.update(vm_data)
                break

    for vm in vms:
        await vm.update_export_task(session, url, sid)

    for future in VirtualMachine.update_futures:
        future.set_result(None)
    VirtualMachine.update_futures = []


async def power_off_vm(session, url, sid, vm):
    await dsm_request(
        session,
        f'{url}/webapi/entry.cgi',
        params={
            '_sid': sid,
            'api': 'SYNO.Virtualization.API.Guest.Action',
            'version': '1',
            'method': 'shutdown',
            'guest_name': vm.guest_name
        }
    )


async def power_on_vm(session, url, sid, vm):
    while True:
        try:
            r = await dsm_request(
                session,
                f'{url}/webapi/entry.cgi',
                params={
                    '_sid': sid,
                    'api': 'SYNO.Virtualization.API.Guest.Action',
                    'version': '1',
                    'method': 'poweron',
                    'guest_name': vm.guest_name
                },
                timeout=10*60,
                ignore_error=True
            )
            if r['success']:
                break
            elif r['error']['code'] == 904:  # Machine is already running
                break
        except asyncio.TimeoutError:
            pass


async def start_vm_export(session, url, sid, vm, path):
    r = await dsm_request(
        session,
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
    )
    return r['data']['task_id']


async def delete_old_export(session, url, sid, vm, path):
    await dsm_request(
        session,
        f'{url}/webapi/entry.cgi',
        params={
            '_sid': sid,
            'api': 'SYNO.FileStation.Delete',
            'version': '2',
            'method': 'delete',
            'path': f'{path}/{vm.guest_name}.ova'
        }
    )


async def export_vm(session, url, sid, vm, path):
    initial_status = vm.status

    logger.info(f'[{vm.guest_name}] Deleting old export, if it exists...')
    await delete_old_export(session, url, sid, vm, path)

    if vm.status != 'shutdown':
        logger.info(f'[{vm.guest_name}] Powering off VM...')
        await power_off_vm(session, url, sid, vm)
        await vm.wait_for_status('shutdown')

    logger.info(f'[{vm.guest_name}] Starting VM export...')
    vm.export_task_id = await start_vm_export(session, url, sid, vm, path)
    logger.debug(f'[{vm.guest_name}] Export task ID: {vm.export_task_id}')

    logger.info(f'[{vm.guest_name}] Waiting for export to finish...')
    await vm.wait_for_export()
    logger.info(f'[{vm.guest_name}] Export finished')
    await report_export_error(vm)

    if initial_status != 'running':
        return  # Don't restart a VM that wasn't running

    logger.info(f'[{vm.guest_name}] Powering on VM...')
    await power_on_vm(session, url, sid, vm)
    await vm.wait_for_status('running')
    logger.info(f'[{vm.guest_name}] VM powered on.')


async def report_export_error(vm):
    if vm.export_task.get('error', {}).get('code') == 1000:
        return  # Unable to find task_id, not an export error
    if not vm.export_task.get('data', {}).get('success', False):
        logger.error(f'Failed exporting {vm.guest_name}.')
        error_code = vm.export_task.get('data', {}).get('task_info', {}) \
            .get('error')
        if error_code:
            logger.error(f'Task failed with error code {error_code}')
            reason = dsm_errors['SYNO.Virtualization'].get(error_code)
            if reason:
                logger.warning(f'Error: {reason}')
        logger.error(f'Full response from DSM: {json.dumps(vm)}')


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
    p.add('--log-level', required=False, default='INFO',
          help='Log verbosity.')
    return p.parse_args()
