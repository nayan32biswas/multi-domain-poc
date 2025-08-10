# Multi-Domain POC - Simplified Architecture Diagram

## ASCII Architecture Overview

```txt
                                Internet
                                    |
                           ┌─────────────────┐
                           │      Nginx      │
                           │  Reverse Proxy  │
                           │   + SSL/HTTPS   │
                           └─────────────────┘
                                    |
                ┌───────────────────┼───────────────────┐
                │                   │                   │
        api.example.com      *.example.com      custom-domains
                │                   │                   │
                ▼                   ▼                   ▼
        ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
        │ API Server  │     │Static Server│     │Static Server│
        │ Port: 8000  │     │ Port: 8080  │     │ Port: 8080  │
        │             │────▶│             │     │             │
        │ - Projects  │     │ - Content   │     │ - Content   │
        │ - Domains   │     │ - Routing   │     │ - Routing   │
        │ - Verify    │     │ - Files     │     │ - Files     │
        └─────────────┘     └─────────────┘     └─────────────┘
                │                   │                   │
                │           ┌───────┴───────┐           │
                │           │               │           │
                ▼           ▼               ▼           ▼
        ┌─────────────────────────────────────────────────────┐
        │                  MongoDB                            │
        │              Database Storage                       │
        │    - Project metadata                               │
        │    - Subdomain mappings                             │
        │    - Custom domain associations                     │
        │    - Verification status                            │
        └─────────────────────────────────────────────────────┘
                │
                │ HTTP Calls
                ▼
        ┌─────────────┐     ┌──────────────────────────────────┐
        │Script Exec  │────▶│         Shell Scripts            │
        │Port: 9090   │     │  - configure-custom-domain.sh    │
        │             │     │  - remove-custom-domain-config   │
        │- SSL Certs  │     │                                  │
        │- Nginx Conf │     │ ┌─────────────────────────────┐  │
        │- Automation │     │ │         Certbot             │  │
        └─────────────┘     │ │    (Let's Encrypt)          │  │
                            │ │  - Wildcard: *.example.com  │  │
                            │ │  - Custom domain certs      │  │
                            │ └─────────────────────────────┘  │
                            └──────────────────────────────────┘

        ┌─────────────┐
        │   Frontend  │
        │  React App  │ ───── Built static files ────▶ /static/
        │  (Dev: 3000)│
        └─────────────┘

```

## Request Flow Diagrams

### 1. Subdomain Access Flow

```txt
User Request: https://abc.example.com
    │
    ▼
┌─────────┐    Route by     ┌─────────────┐    Query by     ┌─────────┐
│  Nginx  │────────────────▶│Static Server│────────────────▶│ MongoDB │
│         │   subdomain     │   :8080     │   subdomain     │         │
└─────────┘                 └─────────────┘                 └─────────┘
    │                               │                               │
    │                               ▼                               │
    │                       ┌─────────────┐                         │
    │                       │ Static Files│◀────────────────────────┘
    │                       │  /static/   │     Return project data
    │                       └─────────────┘
    │                               │
    │                               ▼
    └─────── Serve Content ─────────┘
```

### 2. Custom Domain Setup Flow

```txt
User API Call: POST /api/projects/{id}/custom-domain
    │
    ▼
┌─────────────┐    Generate     ┌─────────┐
│ API Server  │─────────────────▶│MongoDB │
│   :8000     │  verification   │ :27017  │
└─────────────┘     token       └─────────┘
    │
    │ Return TXT record details
    ▼
User adds TXT record to DNS Provider
    │
    ▼
User calls: POST /api/projects/{id}/verify-domain
    │
    ▼
┌─────────────┐    Verify DNS   ┌─────────────┐
│ API Server  │─────────────────▶│ DNS Lookup  │
│   :8000     │    TXT record   │   Service   │
└─────────────┘                 └─────────────┘
    │
    │ On verification success
    ▼
┌─────────────┐    HTTP Call    ┌─────────────┐
│ API Server  │─────────────────▶│Script Exec  │
│   :8000     │   configure     │   :9090     │
└─────────────┘                 └─────────────┘
                                        │
                                        ▼
                                ┌─────────────┐
                                │   Certbot   │
                                │ + Nginx     │
                                │ Config Gen  │
                                └─────────────┘
```

### 3. Data Flow Architecture

```txt
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Request   │    │  Response   │    │   Storage   │
│    Layer    │    │    Layer    │    │    Layer    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Nginx    │    │ FastAPI     │    │   MongoDB   │
│  Port: 443  │    │ Responses   │    │ Port: 27017 │
│  Port: 80   │    │   - JSON    │    │             │
│             │    │   - HTML    │    │ Collections:│
│ Routes:     │    │   - Static  │    │ - projects  │
│ - API calls │    │             │    │             │
│ - Static    │    │ Middleware: │    │ Schema:     │
│ - Custom    │    │ - CORS      │    │ - subdomain │
│             │    │ - TrustedHost│   │ - custom_dm │
└─────────────┘    └─────────────┘    │ - verified  │
                                      └─────────────┘
```

## Network Topology

```txt
                    ┌─────────────────────────────────────┐
                    │            Server Host              │
                    │                                     │
  Internet          │  ┌─────────┐  ┌─────────────────┐   │
      │             │  │  Nginx  │  │   Docker        │   │
      │             │  │ Port 80 │  │   Network       │   │
      ▼             │  │Port 443 │  │                 │   │
┌─────────┐         │  └─────────┘  │ ┌─────────────┐ │   │
│   DNS   │         │       │       │ │ API Server  │ │   │
│Provider │         │       ▼       │ │   :8000     │ │   │
└─────────┘         │  ┌─────────┐  │ └─────────────┘ │   │
      │             │  │Local IPs│  │                 │   │
      │ TXT/CNAME   │  │  :8000  │  │ ┌─────────────┐ │   │
      │ Records     │  │  :8080  │  │ │Static Server│ │   │
      ▼             │  │  :9090  │  │ │   :8080     │ │   │
┌─────────┐         │  │  :27017 │  │ └─────────────┘ │   │
│Users/   │         │  └─────────┘  │                 │   │
│Browsers │         │               │ ┌─────────────┐ │   │
└─────────┘         │               │ │  MongoDB    │ │   │
                    │               │ │   :27017    │ │   │
                    │               │ └─────────────┘ │   │
                    │               └─────────────────┘   │
                    │                                     │
                    │  ┌─────────────────────────────┐    │
                    │  │     Script Executor         │    │
                    │  │        :9090                │    │
                    │  │                             │    │
                    │  │ ┌─────────────────────────┐ │    │
                    │  │ │    System Scripts       │ │    │
                    │  │ │ - configure-domain.sh   │ │    │
                    │  │ │ - remove-domain.sh      │ │    │
                    │  │ │ - certbot commands      │ │    │
                    │  │ └─────────────────────────┘ │    │
                    │  └─────────────────────────────┘    │
                    └─────────────────────────────────────┘
```

This simplified ASCII representation shows the same architectural concepts as the Mermaid diagram but in a format that's easily viewable in any text editor or terminal.
