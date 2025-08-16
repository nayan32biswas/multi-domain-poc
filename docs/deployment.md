# Deploy the app in the server

## Server Setup

We are using `Ubuntu` Server to configure our app. Your command might change based on the server configuration.

We need to install Docker to run the app. Follow the [official doc](https://docs.docker.com/engine/install/ubuntu/) to install Docker on the server.

Create isolated folders for the application.

- `sudo mkdir /opt/md_app` It's like a container for the app. All of the additional server-only information will be there.
- `sudo mkdir /opt/md_app/multi-domain` Actual application folder.
- `sudo mkdir /opt/md_app/prod_data` Optional to store server related information.

Create a zip file of the project on your local device.

```sh
tar --exclude='.git' --exclude='.vscode' --exclude='.env*' \
    --exclude='.venv' --exclude='.pytest_cache' --exclude='.ruff_cache' \
    --exclude='frontend/node_modules' --exclude='frontend/dist' --exclude='frontend/.env*' \
    -czf project.tar.gz -C ./multi-domain .
```

Upload the zip file to the server `scp project.tar.gz  <multi-domain>:./`

Extract the zip file and copy to the project folder `sudo tar --overwrite -xzf ~/project.tar.gz -C /opt/md_app/multi-domain/`

For my case, I have some files that might be different on the server. Here is the command to copy/replace those files. Use it based on your use case.

```sh
cd /opt/md_app/prod_data/ && \
    printf "%s\n" ".env" ".env.caddy" "frontend/.env" "config/Caddyfile" \
  | sudo tar --files-from=- --ignore-failed-read -cf - \
  | sudo tar -xpf - -C /opt/md_app/multi-domain/ && \
  cd /opt/md_app/multi-domain/
```

## DNS Server Configuration

**Add API host:**

```sh
Type: "A Record"
Host: "api.example.com"
Value: <server_ip_address>
```

**Add Wildcard Record:**

```sh
Type: "A Record"
Host: "*.example.com"
Value: <server_ip_address>
```

Some DNS providers, like NameCheap, add the domain name automatically for the host section. For that type of service, we can ignore adding a domain to the host. Like `api` instead of `api.example.com` and `*` instead of `*.example.com`.

For the subdomain configuration, we need some API keys from your DNS provider for the automatic https. We are using NameCheap as our DNS provider. Follow this GitHub account [caddy-dns](https://github.com/caddy-dns). You will find the configuration for different DNS services.

**NameCheap API Token:**

For the subdomain DNS-01 challenge, we need to create some API Keys from the NameCheap service. Follow this [doc](https://www.namecheap.com/support/api/intro/) to get those credentials.

## Running the App

- `docker volume create multi_domain_db` Create an external volume for the database
- `docker volume create multi_domain_caddy_data` Create an external volume for the reverse proxy server
- `docker compose -f docker-compose-prod.yml build server static_server proxy_server` Build the services.
- `docker compose -f docker-compose-prod.yml up -d server static_server proxy_server` Start the services.

Run this command `docker compose -f docker-compose-prod.yml up -d proxy_server` to start the proxy_server server. We need to restart this service if the configuration related to Caddy reverse proxy changes.
