export const isDevelopment = import.meta.env.DEV;

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const DEV_SUBDOMAIN = "localhost";

const getSubdomain = () => {
  const host = window.location.host;
  if (host.includes("localhost") || host.includes("127.0.0.1"))
    return DEV_SUBDOMAIN;

  const domainParts = host.split(".");

  if (domainParts[0] === "www") return domainParts[1];
  if (!domainParts[0]) return "";

  return domainParts[0];
};

export const SUBDOMAIN = getSubdomain().toLocaleLowerCase();
