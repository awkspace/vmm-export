#!/bin/sh
set -euo pipefail

echo "$VME_CRON /usr/bin/vmm-export" > /var/spool/cron/crontabs/root
if [ $# -eq 0 ]
then
    exec /usr/sbin/crond -f
else
    exec "$@"
fi
