# vmm-export

Synology has a virtual machine solution and several off-site backup solutions,
but they don’t cooperate with one another for [some
reason](https://www.synology.com/en-us/products/VMMPro_License_Pack). This
project exports VMs to `.ova` format, which can then be backed up via Hyper
Backup or another solution. Note that, due to the way exporting works, VMs will
be shut down for the duration of the export.

To use the container, make sure you have the Docker app installed on your
DSM.

## Usage as a container (easiest)

### 1. Create a new user.

Navigate to `Control Panel` > `User` and create a new user that will handle the
automatic export. Make sure it has access to Virtual Machine Manager and the
share you’ll be exporting the VMs to.

If the new user is not an admin account, you’ll also need to add it as a manager
to the VMs you wish to export: `Virtual Machine Manager` > `Virtual Machine` >
Select a machine > `Action` > `Edit` > `Permissions`.

### 2. Add the Docker image.

Navigate to `Docker` > `Image` and add `awkspace/vmm-export`.

### 3. Launch the Docker image.

Select `awkspace/vmm-export` and press `Launch`. Go into `Advanced Settings` and
check `Enable auto-restart`. Then go to the `Environment` tab and [configure
vmm-export.](#configuration)

## Usage as command line utility (if running from another machine)

```bash
pip3 install vmm-export
vmm-export --help
```

## Configuration

|Environment (container)|Flag (cli)|Default|Required?|Description|
|:-|:-|:-|:-|:-|
|`VME_USERNAME`|`--username`|None|Yes|The username to use for logging into the DSM.|
|`VME_PASSWORD`|`--password`|None|Yes|The password to use for logging into the DSM.|
|`VME_DSM_URL`|`--dsm-url`|None|Yes|URL of the DSM, including port, e.g. `192.168.1.100:5000`.|
|`VME_PATH`|`--path`|None|Yes|The path to export VMs to, e.g. `/MyShareName/VMM`.|
|`VME_CRON`|N/A|`0 0 * * * `|No|(Container only) [Cron expression](https://www.freeformatter.com/cron-expression-generator-quartz.html) to schedule the export. Make sure to set `TZ` if you want this to be evaluated for [a different timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) than `UTC`.|
|`VME_WORKERS`|`--workers`|`1`|No|How many VMs should be exported in parallel. Because exporting is a CPU intensive process, you should leave this to `1` unless you have a beefy DSM.|
|`VME_EXCLUDE`|`--exclude`|None|No|Comma-separated list of VM names to avoid exporting. By default, `vmm-export` will export all VMs.|
|`VME_INCLUDE`|`--include`|None|No|Comma-separated list of VM names to export. `vmm-export` will only export these VMs. **Note:** This takes precedence over the exclude list.|
|`VME_LOG_LEVEL`|`--log-level`|`WARNING`|No|Set logging level for `vmm-export`.|
