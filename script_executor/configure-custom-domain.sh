#!/bin/bash

# Exit on any error
set -e

CUSTOM_DOMAIN="$1"
CUSTOM_DOMAIN_EMAIL="$2"
IS_DEBUG="$3"
CUSTOM_DOMAIN_TEMPLATE_FILE="/etc/nginx/custom-domain-https-conf.template"
NGINX_CONF_FILE="/etc/nginx/conf.d/custom_domain/$CUSTOM_DOMAIN.conf"

if [ "$IS_DEBUG" ]; then
  echo "Dev mode script. Script executed."
  exit 0
fi

validate_requirements() {
  # Raise error without sudo privileges
  if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root or with sudo privileges."
    return 1
  fi

  # Check if nginx is installed
  if ! command -v nginx &> /dev/null; then
    echo "Nginx is not installed. Please install Nginx and try again."
    return 1
  fi

  # Check if certbot is installed
  if ! command -v certbot &> /dev/null; then
    echo "Certbot is not installed. Please install Certbot and try again."
    return 1
  fi

  # Check required parameters
  if [ -z "$CUSTOM_DOMAIN" ] || [ -z "$CUSTOM_DOMAIN_EMAIL" ]; then
    echo "Usage: $0 <custom-domain> <email>"
    return 1
  fi
  
  return 0
}

obtain_ssl_certificate() {
  local domain="$1"
  local email="$2"
  
  # Check if certificate already exists for the domain
  if certbot certificates | grep -q "$domain"; then
    echo "Certificate already exists for $domain, using existing certificate"
  else
    # Request for SSL certificate from certbot
    echo "No existing certificate found, requesting new SSL certificate for $domain"
    if ! certbot certonly --nginx \
      -d "$domain" \
      --cert-name "$domain" \
      --non-interactive \
      --agree-tos \
      --email "$email"; then
      echo "Failed to obtain SSL certificate for $domain"
      return 1
    fi
  fi
  
  return 0
}

setup_nginx_config() {
  local domain="$1"
  local template_file="$2"
  local conf_file="$3"
  
  # Check if configuration file already exists
  if [ ! -f "$conf_file" ]; then
    # Create directory if it doesn't exist
    mkdir -p "$(dirname "$conf_file")"
    
    # Copy the template and replace the domain placeholder
    cp "$template_file" "$conf_file"
    sed -i "s/CUSTOM_DOMAIN/$domain/g" "$conf_file"
    echo "Created Nginx configuration file: $conf_file"
  else
    echo "Nginx configuration file already exists: $conf_file"
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

  return 0
}


if ! validate_requirements; then
  exit 1
fi

if ! obtain_ssl_certificate "$CUSTOM_DOMAIN" "$CUSTOM_DOMAIN_EMAIL"; then
  exit 1
fi

if ! setup_nginx_config "$CUSTOM_DOMAIN" "$CUSTOM_DOMAIN_TEMPLATE_FILE" "$NGINX_CONF_FILE"; then
  exit 1
fi
