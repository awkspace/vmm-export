# vmm-export

[![Pulls from DockerHub](https://img.shields.io/docker/pulls/awkspace/vmm-export.svg)](https://hub.docker.com/r/awkspace/vmm-export)

Synology has a virtual machine solution and several off-site backup solutions,
but they don’t cooperate with one another for [some
reason](https://www.synology.com/en-us/products/VMMPro_License_Pack). This
project exports VMs to `.ova` format, which can then be backed up via Hyper
Backup or another solution. Note that, due to the way exporting works, VMs will
be shut down for the duration of the export.

To use the container, make sure you have the Docker app installed on your
DSM.

## Usage

### 1. Create a new user.

Navigate to `Control Panel` > `User` and create a new user that will handle the
automatic export. Add this user to the default administrators group.

### 2. Add the Docker image.

Navigate to `Docker` > `Image` and add `awkspace/vmm-export`.

### 3. Launch the Docker image.

Select `awkspace/vmm-export` and press `Launch`. Go into `Advanced Settings` and
check `Enable auto-restart`. Then go to the `Environment` tab and [configure
vmm-export.](#configuration)

## Configuration

This project uses [ConfigArgParse](https://github.com/bw2/ConfigArgParse). If
you’re running `vmm-export` locally (instead of in a container on your DiskStation), you
can use CLI flags or a configuration file to pass options too.

|Environment variable|Default|Required?|Description|
|:-|:-|:-|:-|
|`VME_USERNAME`|None|Yes|The username to use for logging into the DSM.|
|`VME_PASSWORD`|None|Yes|The password to use for logging into the DSM.|
|`VME_DSM_URL`|None|Yes|URL of the DSM, including port, e.g. `192.168.1.100:5000`.|
|`VME_PATH`|None|Yes|The path to export VMs to, e.g. `/MyShareName/VMM`.|
|`VME_CRON`|`0 0 * * * `|No|[Cron expression](https://www.freeformatter.com/cron-expression-generator-quartz.html) to schedule the export. Make sure to set `TZ` if you want this to be evaluated for [a different timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) than `UTC`.|
|`VME_WORKERS`|`1`|No|How many VMs should be exported in parallel. Because exporting is a CPU intensive process, you should leave this to `1` unless you have a beefy DiskStation.|
|`VME_EXCLUDE`|None|No|Comma-separated list of VM names to avoid exporting. By default, `vmm-export` will export all VMs.|
|`VME_INCLUDE`|None|No|Comma-separated list of VM names to export. `vmm-export` will only export these VMs. **Note:** This takes precedence over the exclude list.|
|`VME_LOG_LEVEL`|`WARNING`|No|Set logging level for `vmm-export`.|
