# **Stocky \- Comprehensive Project Brief**

Version: 1.0 (Consolidated)  
Date: August 5, 2025

## **1\. Project Overview**

**Stocky** is a home kitchen inventory management system designed to track food and other household goods. It utilizes a barcode scanner and a touch-friendly user interface to simplify the process of adding, removing, and locating items. The system is built with a flexible, multi-user, service-oriented architecture to allow for multiple user interfaces and future expansion. The project is intended to be open-source under the **MIT License**.

## **2\. Technology Stack**

* **Backend:** Python 3.11+, FastAPI, SQLAlchemy (ORM), Alembic (Migrations), Uvicorn (ASGI Server)  
* **Database:** SQLite (Default), PostgreSQL (Supported)  
* **Touchscreen UI (StockyTouch):** Python, PySide6 (Qt Framework)  
* **Web UI (StockyWeb):** ReactJS  
* **Messaging:** MQTT  
* **Containerization:** Docker, Docker Compose

## **3\. System Architecture**

The Stocky ecosystem is composed of several decoupled services and clients. The core backend is the single source of truth for all data and state, communicating with clients via a REST API and WebSockets.

* **Hardware Input:** Wireless 1D/2D barcode scanners.  
* **Message Broker:** An existing MQTT server.  
* **MQTT Bridge Service:** A stateless microservice that translates MQTT messages into REST API calls to the main backend. It will be its own independent project.  
* **Backend Application (Stocky):** The primary Python application. It manages all data and state, exposing a REST API for data operations and a WebSocket interface for real-time UI notifications.  
* **Frontend Clients (StockyTouch, StockyWeb):** UI applications that interact with the backend.

## **4\. Data Model**

### **4.1. User**

Uses a flexible JSON field for state and other details.

| Field | Type | Description |
| :---- | :---- | :---- |
| id | UUID | Primary Key. |
| username | String(255) | Unique login name. |
| password\_hash | String | Hashed password for human users. |
| api\_key | String | Unique API key for scanners/services. |
| role | String(50) | 'Admin', 'Member', 'Scanner', 'Read-only'. |
| details | JSON | Flexible, type-specific data. |

**Example details for a 'Scanner' user:**

{  
  "current\_mode": "add",  
  "current\_location\_id": "uuid-of-location",  
  "last\_scan\_timestamp": "...",  
  "associated\_ui\_id": "uuid-of-ui-instance"  
}

### **4.2. Item**

| Field | Type | Description |
| :---- | :---- | :---- |
| id | UUID | Primary Key. |
| name | String(255) | Human-readable name. Can be null initially. |
| description | Text | Longer description of the item. |
| upc | String(48) | UPC barcode number. Alternate identifier. |
| storage\_type | String(50) | 'Ambient', 'Refrigerated', 'Frozen'. |

### **4.3. Location**

| Field | Type | Description |
| :---- | :---- | :---- |
| id | UUID | Primary Key. |
| name | String(255) | Human-readable name of the location. |
| storage\_type | String(50) | The type of storage this location provides. |
| details | Text | Additional details about the location. |

### **4.4. SKU (Stock Keeping Unit)**

| Field | Type | Description |
| :---- | :---- | :---- |
| id | UUID | Primary Key. |
| item\_id | UUID | Foreign key to Item. |
| location\_id | UUID | Foreign key to Location. |
| quantity | Integer | Current stock count. |
| created\_at | DateTime | Timestamp of creation. |
| updated\_at | DateTime | Timestamp of last quantity modification. |

### **4.5. Alert**

| Field | Type | Description |
| :---- | :---- | :---- |
| id | UUID | Primary Key. |
| timestamp | DateTime | When the alert was generated. |
| severity | String(50) | 'Warning', 'Info', 'Error'. |
| message | Text | The content of the alert message. |
| is\_acknowledged | Boolean | Whether a user has acknowledged the alert. |

### **4.6. Log**

| Field | Type | Description |
| :---- | :---- | :---- |
| id | UUID | Primary Key. |
| timestamp | DateTime | When the event occurred. |
| severity | String(50) | 'INFO', 'WARN', 'ERROR'. |
| message | Text | The content of the log message. |
| source | String(255) | The source of the event (e.g., 'Scanner: Kitchen'). |

## **5\. Key Workflows & Business Logic**

### **5.1. Scanner Input & State Management**

* The scanner's configurable id field will be set to its user's API key.  
* The MQTT Bridge receives messages (e.g., {"id":"API\_KEY","msg":"SCAN\_DATA"}), and makes a POST /scanner/scan call to the backend, passing the key in the X-API-Key header.  
* The backend is responsible for all state management. It looks up the scanner user by API key, retrieves its current state from user.details, processes the scan, and updates the state.  
* The default scanner mode is 'add' and it does not time out.

### **5.2. Scanner to UI Communication**

1. A StockyTouch instance starts and establishes a WebSocket connection with the backend, identifying itself with a unique ui\_instance\_id.  
2. The UI displays a QR code containing {"command": "associate\_ui", "payload": "ui\_instance\_id"}.  
3. A user scans this QR code with a physical scanner.  
4. The backend receives this command and updates the scanner's user.details to include the associated\_ui\_id.  
5. Later, the user scans a UI command (e.g., {"command": "show\_view", "payload": "log"}).  
6. The backend identifies the scanner, retrieves its associated UI ID, and sends a command down the corresponding WebSocket.  
7. The StockyTouch instance receives the command and executes it (e.g., switches to the Log tab).

### **5.3. Data Handling**

* **New UPCs:** When an unrecognized UPC is scanned, an Item is created with a NULL name. An asynchronous background job is queued to query an external **UPC Data Application (UDA)** to populate the name/description.  
* **Storage Mismatch:** If an item is added to a location with a mismatched storage\_type, the action succeeds, but a Warning level Alert is generated.  
* **Data Deletion:**  
  * **Items:** An Item is never truly deleted. When its total quantity reaches zero, it is considered "hidden" and excluded from default views. A permanent deletion option is available to Admins from the "Zero Stock" view.  
  * **Locations:** A Location can only be deleted if it is empty. The UI is responsible for orchestrating a "move" workflow to empty the location before deletion.  
  * **SKUs:** A SKU remains in the UI when its quantity is zero. It can be manually deleted from the "Item Details" page.  
* **Search:** Inventory search will be comprehensive, querying all fields on the Item model (name, description, upc, id).

## **6\. API Specification**

### **6.1. WebSocket API**

* **Endpoint:** /ws  
* **Protocol:** Establishes a WebSocket connection.  
* **Client-to-Server:** Client sends an initial message: {"action": "identify\_ui", "ui\_id": "unique-uuid-for-instance"}.  
* **Server-to-Client:** Server pushes commands: {"action": "show\_view", "view": "log"}.

### **6.2. REST API**

All endpoints are prefixed with /api/v1.

* **Scanner Interaction:**  
  * POST /scanner/scan: Primary endpoint for all scanner input.  
* **State Management:**  
  * GET /scanner/status: Returns the current state of all scanner users.  
  * PUT /scanner/{id}/state: Allows an Admin to manually update a scanner's state.  
* **Core Data Models (CRUD):**  
  * Standard CRUD endpoints are provided for Item, Location, SKU, User, Alert.  
  * GET /log: Retrieves log entries with query filters (?severity=, ?search=).  
* **Functional Endpoints:**  
  * POST /auth/login: Authenticates a human user and returns a JWT.  
  * POST /item/{id}/refresh: Triggers an async job to query the UDA.  
  * GET /qr/item/{id}: Returns a QR code image for an item's UUID.  
  * POST /qr/command: Generates a QR code for a specific command payload.

## **7\. Frontend Client Design (StockyTouch)**

The UI will be a tabbed interface with a persistent top bar (user info, alerts) and bottom status bar (scanner states).

* **Tabs:**  
  * **Inventory (Default):** An accordion-style list of items. Collapsed rows show item name and total quantity. Expanded rows show quantity per location with \[+/-\] buttons for quick adjustment.  
  * **Locations:** CRUD interface for managing locations.  
  * **Scanners:** Admin view to remotely see and change the state (mode/location) of each scanner.  
  * **Log:** A filterable, searchable view of system events from the in-memory log cache.  
  * **Users:** Admin interface for managing users, roles, and API keys.  
* **Item Details Page:** A dedicated page for viewing/editing all details of a single item and managing its SKUs.  
* **Shopping List:** The "Zero Stock" filter on the Inventory tab serves as a shopping list, sorted by last update time.

## **8\. Backend Application & Environment**

### **8.1. Directory Structure**

A standard, installable Python package structure with a src layout will be used.

### **8.2. Configuration Files**

#### **pyproject.toml**

\[project\]  
name \= "stocky"  
version \= "0.1.0"  
authors \= \[  
    { name \= "Your Name", email \= "you@example.com" },  
\]  
description \= "A home kitchen inventory management system."  
requires-python \= "\>=3.11"  
dependencies \= \[  
    "fastapi",  
    "uvicorn\[standard\]",  
    "sqlalchemy",  
    "alembic",  
    "pydantic",  
    "pydantic-settings",  
    "passlib\[bcrypt\]",  
    "python-jose\[cryptography\]",  
    "websockets",  
    "httpx",  
\]

\[project.optional-dependencies\]  
postgres \= \["psycopg2-binary"\]  
dev \= \["pytest", "pytest-cov"\]

\[tool.setuptools.packages.find\]  
where \= \["src"\]

#### **Dockerfile**

\# Stage 1: Build stage  
FROM python:3.11-slim as builder  
WORKDIR /app  
RUN pip install uv  
COPY pyproject.toml ./  
RUN uv pip install \--system \--no-cache \--no-deps \-p pyproject.toml  
COPY ./src ./src

\# Stage 2: Final production stage  
FROM python:3.11-slim  
WORKDIR /app  
RUN useradd \--create-home appuser  
USER appuser  
COPY \--from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages  
COPY \--from=builder /usr/local/bin /usr/local/bin  
COPY \--chown=appuser:appuser ./src ./src  
VOLUME /app/data  
EXPOSE 8000  
CMD \["uvicorn", "stocky.main:app", "--host", "0.0.0.0", "--port", "8000"\]

#### **docker-compose.yml**

version: '3.8'

services:  
  backend:  
    build: .  
    ports:  
      \- "8000:8000"  
    volumes:  
      \- ./src:/app/src  
      \- stocky\_data:/app/data  
    env\_file:  
      \- .env

volumes:  
  stocky\_data:

#### **.env.example**

\# Default database URL points to a file inside the 'data' volume.  
DATABASE\_URL="sqlite+aiosqlite:///./data/stocky.db"

\# For JWT token creation (generate with: openssl rand \-hex 32\)  
SECRET\_KEY="\<your secret key here\>"

\# The URL for the external UPC Data Application  
UDA\_API\_URL="http://example.com/product"

### **8.3. Development & Lifecycle**

* **Testing:** A multi-layered testing strategy using pytest will cover unit, integration, and API tests.  
* **Migrations:** Database schema changes will be managed using **Alembic**.  
* **Logging:** Logs will be pushed to an in-memory deque with a maxlen of 10,000, which serves the /log API endpoint.  
* **Data Seeding:** An initial script (initial\_data.py) will be provided to create the first Admin user. A separate, optional script will be available to generate comprehensive demo data.