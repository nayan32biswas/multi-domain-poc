# Multi Domain POC

This is a proof-of-concept project on how wildcard domains work. Additionally, we added a way to support a custom domain. We will be able to add a custom domain if they want to. For simplicity, we made the app simple since it's a POC project. On our frontend side, you are only allowed to view the created project and update some information about the existing project.

We can use the API to create a project. Each project will work like an independent app. Where each project will have a subdomain. With that subdomain, we can access our newly created project data. The subdomain will be abc.example.com. Also, we can integrate our custom domain with a project.

## Simple steps to create project

- Open the url like `localhost:8000/docs` or `api.example.com/docs` in the browser.
- You will see bunch of API. User `/api/projects/` to create a project.
- After creating the project you can access the project with your newly added subdomain. For example `abc.example.com` where *abc* is your subdomain.

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
