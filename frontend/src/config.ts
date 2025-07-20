export const isDevelopment = import.meta.env.DEV;

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const SITE_DOMAIN = import.meta.env.VITE_SITE_DOMAIN;

const DEV_SUBDOMAIN = "localhost";

const getHost = () => {
  if (isDevelopment) {
    return DEV_SUBDOMAIN;
  }

  const host = window.location.host;

  if (host.startsWith("www.")) {
    return host.slice(4);
  }

  if (host.startsWith(DEV_SUBDOMAIN)) {
    return DEV_SUBDOMAIN;
  }

  return host;
};

const getSubdomain = () => {
  const host = getHost();
  if (host === DEV_SUBDOMAIN) return DEV_SUBDOMAIN;

  if (host.includes(SITE_DOMAIN)) return "";

  const domainParts = host.split(".");

  if (domainParts[0] === "www") return domainParts[1];
  if (!domainParts[0]) return "";

  return domainParts[0];
};

export const CUSTOM_DOMAIN = getHost().toLowerCase();
export const SUBDOMAIN = getSubdomain().toLowerCase();
