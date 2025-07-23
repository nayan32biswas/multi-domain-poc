# Server Setup

This document will walk you through how to set up the Nginx proxy server to serve API and static content for the wildcard subdomain system.
Additionally, we will set up a custom domain configuration with nginx (without `HTTPS`).

We assume your API service is running at port **8000** on the same machine.
And your static file server is running on port **8080** on the same machine.

## Install Certbot

Install Snap

```sh
sudo apt update
sudo apt install snapd
sudo snap install core
sudo snap refresh core
```

```sh
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

## Install Nginx

```sh
sudo apt update && sudo apt install nginx
sudo unlink /etc/nginx/sites-enabled/default
```

## Setup API Server

- `sudo vi /etc/nginx/conf.d/backend-api.conf`

```conf
upstream backend_server {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://backend_server;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Restart nginx service

```sh
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl status nginx
```

Make the api https with certbot

- `sudo certbot --nginx -d api.example.com`

## Setup Reverse Proxy for the wildcard domain

### Get new key by challenge

#### Manual Setup

Some provider does not have automatic tools or API to challenge certificate. Like [NameCheap](https://namecheap.com). We need to request and add the TXT record manually for those services.

```sh
sudo certbot certonly --manual --preferred-challenges dns -d '*.example.com'
```

- It will provide a TXT record.
- The TXT record is need to add to your DNS provider.
- Check if the text record is propagate across the globe by dns checker like `dnschecker.org`.
- Continue

New pem file will be created under the path:

- `/etc/letsencrypt/live/example.com/fullchain.pem`
- `/etc/letsencrypt/live/example.com/privkey.pem`

Later we have to manually review the key.

#### Automatic setup with pre build extensions

Here is an example of how we can get certificate automatically for the cloudflare.

- `sudo apt install python3-certbot-dns-cloudflare`
- `sudo nano /etc/letsencrypt/cloudflare.ini`

```ini
dns_cloudflare_email = your@email.com
dns_cloudflare_api_key = YOUR_CLOUDFLARE_API_KEY
```

- `sudo chmod 600 /etc/letsencrypt/cloudflare.ini`

```sh
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d '*.example.com'
```

New pem file will be created under the path:

- `/etc/letsencrypt/live/example.com/fullchain.pem`
- `/etc/letsencrypt/live/example.com/privkey.pem`

We can use the bellow command to review the key:

- `sudo certbot renew --dry-run`.
- We can set **crontab** command to automatically renew.

### Setup Nginx

- `sudo vi /etc/nginx/conf.d/frontend.conf`

```conf
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name *.example.com;
    return 301 https://$server_name$request_uri;
}

upstream frontend_server {
    server localhost:8080;
}

server {
    listen 443 ssl http2;
    server_name *.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://frontend_server;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```sh
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl status nginx
```

### Custom Domain Configuration

- `sudo vi /etc/nginx/conf.d/custom-domain.conf`

```conf
# This will handle all incoming domains and let FastAPI middleware determine routing
server {
    listen 80;
    server_name _;  # Catch all domains
    ; server_name ~^(?!.*\.example\.com$).*$; # Use this line if you are using the same server to serve static content on wildcard and custom domain.

    # Set client max body size for file uploads
    client_max_body_size 50M;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

```sh
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl status nginx
```
