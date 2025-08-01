# Script Executor

## Run the executor locally

- `uv run -m uvicorn script_executor.main:app --reload --host 0.0.0.0 --port 9090`
- `sudo ufw allow 9090` Allow 9090 port.

## Server Setup

Login to the server.

### Create new user for isolation

- `sudo useradd -m -s /bin/bash scriptexec`
- `sudo visudo -f /etc/sudoers.d/scriptexec`
  - `scriptexec ALL=(ALL) NOPASSWD:ALL` Add this line to the file
- `sudo su - scriptexec` Switch to the user.
- `sudo whoami` Validate sudo access and user

### Install python and packages

```sh
cd /home/scriptexec/

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv --version

# Install targeted python for the user
uv python list
uv python install <full_version_name_from_list>

# Create new folder for the project
sudo mkdir -p /opt/executor
sudo chown -R scriptexec:scriptexec /opt/executor && cd /opt/executor

# Create venv and install packages
uv venv .venv
source .venv/bin/activate
uv pip install -r /opt/executor/requirements.txt
deactivate
```

### Copy file and update permission

```sh
sudo cp -r /path/to/script_executor /opt/executor/
sudo chown -R scriptexec:scriptexec /opt/executor
sudo chmod +x /opt/executor/script_executor/configure-custom-domain.sh
```

### Configure SystemD

`sudo vi /etc/systemd/system/script-executor.service`

```conf
[Unit]
Description=Script Executor API
After=network.target

[Service]
User=scriptexec
Group=scriptexec
WorkingDirectory=/opt/executor
ExecStart=/opt/executor/.venv/bin/uvicorn script_executor.main:app --host 0.0.0.0 --port 9090

# Optional (security, reliability)
Restart=always
RestartSec=30
Environment=PATH=/opt/executor/.venv/bin
Environment=PYTHONUNBUFFERED=1
Environment=DEBUG=False

[Install]
WantedBy=multi-user.target
```

```sh
sudo systemctl daemon-reload
sudo systemctl enable script-executor
sudo systemctl start script-executor
sudo systemctl status script-executor
```

```sh
sudo systemctl stop script-executor
sudo systemctl disable script-executor
```

`sudo ufw allow 9090` Allow 9090 port for the main to call the executor. Should be avoided in production.

### Update the App

- Update the environment variable if required:
  - `sudo vi /etc/systemd/system/script-executor.service`
  - `sudo systemctl daemon-reload`

```sh
sudo su - scriptexec

sudo cp -r /path/to/script_executor /opt/executor/
sudo chown -R scriptexec:scriptexec /opt/executor
sudo chmod +x /opt/executor/script_executor/configure-custom-domain.sh

sudo systemctl restart script-executor
```
