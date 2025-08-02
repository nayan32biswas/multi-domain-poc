#!/bin/bash

# Exit on any error
set -e

CUSTOM_DOMAIN="$1"
IS_DEBUG="$3"
CUSTOM_DOMAIN_TEMPLATE_FILE="/etc/nginx/custom-domain-https-conf.template"
NGINX_CONF_FILE="/etc/nginx/conf.d/custom_domain/$CUSTOM_DOMAIN.conf"

if [ "$IS_DEBUG" ]; then
  echo "Dev Mode: Removed configuration for $CUSTOM_DOMAIN."
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
  if [ -z "$CUSTOM_DOMAIN" ]; then
    echo "Usage: $0 <custom-domain>"
    return 1
  fi

  return 0
}

remove_nginx_configuration() {
  local domain="$1"

  # Check if the configuration file exists
  if [ -f "$NGINX_CONF_FILE" ]; then
    echo "Removing Nginx configuration for $domain"
    rm -f "$NGINX_CONF_FILE"
  else
    echo "No Nginx configuration found for $domain"
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

remove_ssl_certificate() {
  local domain="$1"

  # Check if the certificate exists for the domain
  if certbot certificates | grep -q "$domain"; then
    echo "Removing SSL certificate for $domain"
    if ! certbot delete --cert-name "$domain" --non-interactive; then
      echo "Failed to delete SSL certificate for $domain"
      return 1
    fi
  else
    echo "No SSL certificate found for $domain"
  fi

  return 0
}


if ! validate_requirements; then
  exit 1
fi

if ! remove_nginx_configuration "$CUSTOM_DOMAIN"; then
  echo "Failed to remove Nginx configuration for $CUSTOM_DOMAIN"
  exit 1
fi

if ! remove_ssl_certificate "$CUSTOM_DOMAIN"; then
  echo "Failed to remove SSL certificate for $CUSTOM_DOMAIN"
  exit 1
fi
