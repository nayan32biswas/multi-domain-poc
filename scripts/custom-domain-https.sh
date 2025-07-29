#!/bin/bash

# Exit on any error
set -e

# Raise error without sudo privileges
if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root or with sudo privileges."
  exit 1
fi

CUSTOM_DOMAIN="$1"
CUSTOM_DOMAIN_EMAIL="$2"
CUSTOM_DOMAIN_TEMPLATE_FILE="/etc/nginx/custom-domain-https-conf.template"
NGINX_CONF_FILE="/etc/nginx/conf.d/custom_domain/$CUSTOM_DOMAIN.conf"

if [ -z "$CUSTOM_DOMAIN" ] || [ -z "$CUSTOM_DOMAIN_EMAIL" ]; then
  echo "Usage: $0 <custom-domain> <email>"
  exit 1
fi

# Check if certificate already exists for the domain
if certbot certificates | grep -q "$CUSTOM_DOMAIN"; then
  echo "Certificate already exists for $CUSTOM_DOMAIN, using existing certificate"
else
  # Request for SSL certificate from certbot
  echo "No existing certificate found, requesting new SSL certificate for $CUSTOM_DOMAIN"
  if ! certbot certonly --nginx \
    -d "$CUSTOM_DOMAIN" \
    --cert-name "$CUSTOM_DOMAIN" \
    --non-interactive \
    --agree-tos \
    --email "$CUSTOM_DOMAIN_EMAIL"; then
    echo "Failed to obtain SSL certificate for $CUSTOM_DOMAIN"
    exit 1
  fi
fi


# Copy the existing Nginx conf template and replace the domain placeholder
if [ ! -f "$NGINX_CONF_FILE" ]; then
    cp "$CUSTOM_DOMAIN_TEMPLATE_FILE" "$NGINX_CONF_FILE"
    # Replace placeholder with actual domain in the configuration file
    sed -i "s/CUSTOM_DOMAIN/$CUSTOM_DOMAIN/g" "$NGINX_CONF_FILE"
    echo "Created Nginx configuration file: $NGINX_CONF_FILE"
else
    echo "Nginx configuration file already exists: $NGINX_CONF_FILE"
fi

# Check the Nginx configuration for syntax errors
if ! nginx -t; then
    echo "Nginx configuration test failed. Please check the configuration file."
    exit 1
fi

# Reload Nginx to apply the new configuration
if ! nginx -s reload; then
    echo "Failed to reload Nginx. Please check the service status."
    exit 1
fi



"""
sudo certbot certonly --nginx --cert-name neuwark.xyz -d neuwark.xyz --non-interactive --agree-tos --email admin@neuwark.xyz
"""