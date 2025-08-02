# Multi Domain POC

- **Subdomain System**: Configure and manage a subdomain for a multi-tenant application.
- **Custom Domain Integration**: Easy way to integrate custom domain with existing application.

This is a proof-of-concept project on how wildcard domains work. Additionally, we added a way to support a custom domain. We will be able to add a custom domain if they want to. For simplicity, we made the app simple since it's a POC project. On our frontend side, you are only allowed to view the created project and update some information about the existing project.

We can use the API to create a project. Each project will work like an independent app. Where each project will have a subdomain. With that subdomain, we can access our newly created project data. The subdomain will be abc.example.com. Also, we can integrate our custom domain with a project.

## Overall Project Structure

For simplicity, we don't have any authentication, and security best practices are ignored. This is A POC project and not meant to be used in production directly. Most of the things we tried to keep simple.

- **API App**: Will store and manage metadata about the project. This will serve the necessary APIs. We will use a single API to expose the API server like "api.example.com".
- **Script Executor**: This service will be used for internal execution and managing configuration.
- **Static App**: This app will serve the static files to the targeted subdomain or custom domain. In this app, we mainly serve content based on pre-configured data.
- **Data Base**: For simplicity, we are using MongoDB. A single database will be shared between the *API App* and *Static App*.

## Project Flow

For this project, most of the action is taken by the API. We have a simple UI to validate if we can use the project on our targeted domain.

Open the url like `api.example.com/docs` in the browser.

**New Project:**

- Create a project with the API `/api/projects/` method `POST`. It will provide you with the project_id, subdomain, etc.
- You should be able to access the app with `<subdomain>.example.com`.

**Custom Domain:**

- Add a custom domain with the existing project ID. Use the `/api/projects/{project_id}/custom-domain` API to add the custom domain.
- It will respond with a TXT record 'host' and 'value'. Add that record to your domain provider to validate your domain.
- You can use the API `/api/projects/{project_id}/custom-domain/instructions` to get full instructions for the integration.
- Use the API `/api/projects/{project_id}/verify-domain` to validate your domain.
- Use your subdomain to point to the custom domain. For example, CNAME: "host: @, value: subdomain.example.com".
- To remove the custom domain integration, use this API `/api/projects/{project_id}/custom-domain`.

## Integrate custom domain

User the API `/api/projects/{project_id}/custom-domain/instructions` to get instruction on how you can add the custom domain to your DNS provider.

## Start the dev server

- Make copy of the file `example.env` => `.env` for the backend.
- `docker compose up server` Run the backend
- Make copy of the file `frontend/example.env` => `frontend/.env` for the frontend.
- `cd frontend && npm run dev` Run the frontend

## Start the app for build version

- `docker compose up --build frontend-builder` Build frontend.
- `docker compose build server` Build the app image.
- `docker compose up -d server static_server`

## System Documentation

### [Reverse Proxy Setup](./docs/reverse_proxy.md)

### [Script Executor](./docs/script-executor.md)
