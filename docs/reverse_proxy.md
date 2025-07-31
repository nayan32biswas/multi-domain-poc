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
- Copy the nginx conf for the [backend-api.conf](../config/backend-api.conf)

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
- Copy the nginx conf for the [frontend.conf](../config/frontend.conf)

```sh
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl status nginx
```

### Custom Domain Configuration

#### Custom Domain Without HTTPS

- `sudo vi /etc/nginx/conf.d/custom-domain-http.conf`
- [custom-domain-http.conf](../config/custom-domain-http.conf)

```sh
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl status nginx
```

#### Custom Domain With HTTPS

For the custom domain we will use one nginx config for each custom domain. We will issue new certificate for each custom domain from the CertBot.

- `sudo mkdir -p /etc/nginx/conf.d/custom_domain/`
- `sudo vi /etc/nginx/nginx.conf`

```conf
        include /etc/nginx/conf.d/*.conf;   # Existing Code
        include /etc/nginx/sites-enabled/*; # Existing Code

        include /etc/nginx/conf.d/custom_domain/*.conf;
```

- `sudo vi /etc/nginx/custom-domain-https-conf.template`
- Copy the template file content [custom-domain-https-conf.template](../config/custom-domain-https-conf.template)
- `sudo chmod +x ./script_executor/configure-custom-domain.sh`
- `./script_executor/configure-custom-domain.sh example.com admin@example.com` This will be command to generate certificate and nginx config.

- We configured script to automatically issue new certificate and add new nginx configuration from the existing template config.
- `sudo certbot delete --cert-name example.com` Clean up existing certbot certificate if exists.
