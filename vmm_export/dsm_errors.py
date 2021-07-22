#!/usr/bin/env python3

errors = {
    'Generic': {
        100: 'Unknown error',
        101: 'No parameter of API, method or version',
        102: 'The requested API does not exist',
        103: 'The requested method does not exist',
        104: 'The requested version does not support the functionality',
        105: 'The logged in session does not have permission',
        106: 'Session timeout',
        107: 'Session interrupted by duplicate login',
        119: 'SID not found'
    },
    'SYNO.API.Auth': {
        400: 'No such account or incorrect password',
        401: 'Account disabled',
        402: 'Permission denied',
        403: '2-step verification code required',
        404: 'Failed to authenticate 2-step verification code'
    },
    'Syno.Virtualization.API.Guest.Action': {
        401: 'Bad parameter.',
        402: 'Operation failed.',
        403: 'Name conflict.',
        404: 'The number of iSCSI LUNs has reached the system limit.',
        500: 'The cluster is frozen. More than half the hosts are offline.',
        501: 'The cluster is in incompatible mode. Please upgrade to a '
        'compatible DSM version and try again.',
        600: 'The cluster is not ready.',
        601: 'The host is offline.',
        700: 'The storage is invalid.',
        900: 'Failed to set a host to a virtual machine.',
        901: 'The virtual machine does not have a host.',
        902: 'Failed to power on a virtual machine due to insufficient CPU '
        'threads.',
        903: 'Failed to power on a virtual machine due to insufficient '
        'memory.',
        904: 'The status of the virtual machine is online.',
        905: 'MAC conflict.',
        906: 'Failed to create virtual machine because the selected image is '
        'not found.',
        907: 'The status of the virtual machine is offline.',
        908: 'Failed to power on the virtual machine due to insufficient CPU '
        'threads for reservation on the host.',
        909: 'Failed to power on the virtual machine because there is no '
        'corresponding networking on the host.',
        910: 'Only the VirtIO hard disk controller can be used to boot the '
        'virtual machine remotely.',
        1000: 'Cannot find task_id.',
        1001: 'Need Virtual Machine Manager Pro.',
        1400: 'The result of image creating is partial success.',
        1600: 'The virtual machine has been successfully edited. However, '
        'errors occurred while reserving the memory or CPU on the HA hosts.'
    }
}
