from charms.reactive import when, when_not, set_flag, set_state, when_file_changed
from charmhelpers.core.hookenv import open_port, config
from charmhelpers.core.hookenv import status_set
from charmhelpers.core.templating import render
from charmhelpers.core.host import service, service_running, service_available

import urllib.request
import os
import stat


def access_key():
    return str(config('access-key'))


def secret_key():
    return str(config('secret-key'))


@when_not('minio.installed')
def install_minio():
    status_set("maintenance", "Installing MinIO server")

    minio_url = "https://dl.min.io/server/minio/release/linux-amd64/minio"
    minio_binary = "/usr/local/bin/minio"
    
    urllib.request.urlretrieve(minio_url, minio_binary)
    os.chmod(minio_binary, stat.S_IEXEC)

    data_dir = "/data"
    os.mkdir(data_dir)

    set_state('minio.installed')


@when('minio.installed')
def start_minio():
    status_set("maintenance", "Starting MinIO server")

    render(source="minio.service.j2",
           target="/lib/systemd/system/minio.service",
           perms=0o775,
           context={
               "access_key": access_key(),
               "secret_key": secret_key(),
               "data_dir": "/data",
           })

    service("enable", "minio")
    status_set('active', 'MinIO server ready')



@when_file_changed('/lib/systemd/system/minio.service')
def restart():
    open_port(9000)
    if service_running("minio"):
        service("restart", "minio")
    else:
        service("start", "minio")
    status_set("active", "")
