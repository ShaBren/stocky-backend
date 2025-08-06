Stocky Backend - Application & Environment Design
Version: 1.2 (Final)
Date: August 5, 2025

1. Project & Directory Structure
The project will be organized as a standard, installable Python package.

stocky-backend/
│
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── pyproject.toml
├── README.md
│
└── src/
    └── stocky-backend/
        │
        ├── __init__.py
        ├── api/
        ├── core/
        ├── crud/
        ├── db/
        │   ├── alembic/
        │   └── initial\_data.py  # Script to create default admin
        │   └── demo\_data.py  # Script to insert sample data for demo/testing
        ├── models/
        ├── schemas/
        ├── services/
        └── main.py

2. Dependency Management & Licensing
Dependencies will be managed via uv and a requirements.txt file. The project and all its core dependencies will use the MIT License.

3. Configuration Management
Configuration will be managed via environment variables, with SQLite as the default database. PostgreSQL is supported as an optional, user-configured alternative.

4. Application Logging
The /log API endpoint will be served from an in-memory, capped collection (e.g., a collections.deque with a maxlen of 10,000). A custom logging handler will be implemented to push log records into this in-memory store.

5. Dockerization & Deployment
The application is designed to be run as a Docker container. The default docker-compose.yml will be configured for a simple, single-service setup using SQLite, making the initial startup process trivial.

6. Testing Strategy
A multi-layered testing strategy using pytest will be implemented, covering unit, integration, and API tests. Integration tests will run against a temporary, clean test database.

7. Database Migrations
Database schema changes will be managed using Alembic, allowing for version-controlled, incremental updates.

8. Initial Data Seeding
A manual script, src/stocky/db/initial_data.py, will be provided. Its sole purpose is to create the initial Admin user, allowing the administrator to then set up the rest of the system (locations, scanners, etc.) through the UI. An optional, separate script for generating comprehensive demo data can be created for testing and demonstration purposes.
