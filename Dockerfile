FROM alpine:latest

COPY docker-entrypoint.sh /
COPY [ \
    "setup.py", \
    "requirements.txt", \
    "README.md", \
    "/app/" \
]
COPY [ \
    "vmm_export/__init__.py", \
    "vmm_export/cli.py", \
    "vmm_export/virtual_machine.py", \
    "vmm_export/dsm_errors.py", \
    "/app/vmm_export/" \
]

RUN apk add --no-cache \
    tini \
    tzdata \
    py3-yarl \
    py3-pip && \
    pip3 install /app

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/docker-entrypoint.sh"]

ENV VME_CRON '0 0 * * *'
ENV VME_LOG_LEVEL INFO
