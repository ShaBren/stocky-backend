# **Stocky \- System Design Document**

Version: 1.0  
Date: August 5, 2025

## **1\. Introduction**

Stocky is a home kitchen inventory management system designed to track food and other household goods. It utilizes a barcode scanner and a touch-friendly user interface to simplify the process of adding, removing, and locating items. The system is built with a flexible, multi-user, service-oriented architecture to allow for multiple user interfaces and future expansion.

## **2\. System Architecture**

The Stocky ecosystem is composed of several decoupled services and clients. The core backend is the single source of truth for all data and state, communicating with clients via a REST API and WebSockets.

* **Hardware Input:** Wireless 1D/2D barcode scanners.  
* **Message Broker:** An MQTT server.  
* **MQTT Bridge Service:** A stateless microservice that translates MQTT messages into REST API calls to the main backend.  
* **Backend Application (Stocky):** The primary Python application. It manages all data and state, exposing a REST API for data operations and a WebSocket interface for real-time UI notifications.  
* **Frontend Clients (StockyTouch, StockyWeb):** UI applications that interact with the backend.

## **3\. Data Model**

### **3.1. User**

Uses a flexible JSON field for state and other details.

|

| Field | Type | Description |  
| id | UUID | Primary Key. |  
| username | String(255) | Unique login name. |  
| password\_hash | String | Hashed password for human users. |  
| api\_key | String | Unique API key for scanners/services. |  
| role | String(50) | 'Admin', 'Member', 'Scanner'. |  
| details | JSON | Flexible, type-specific data. |  
**Example** details **for a 'Scanner' user:**

{  
  "current\_mode": "add",  
  "current\_location\_id": "uuid-of-location",  
  "last\_scan\_timestamp": "...",  
  "associated\_ui\_id": "uuid-of-ui-instance"  
}

### **3.2. SKU (Stock Keeping Unit)**

Tracks modification times for sorting and "shopping list" functionality.

| Field | Type | Description |  
| id | UUID | Primary Key. |  
| item\_id | UUID | Foreign key to Item. |  
| location\_id | UUID | Foreign key to Location. |  
| quantity | Integer | Current stock count. |  
| created\_at | DateTime | Timestamp of creation. |  
| updated\_at | DateTime | Timestamp of last quantity modification. |

### **3.3. Other Models**

Item, Location, Log, and Alert models are also included as previously defined.

## **4\. Key Workflows & Business Logic**

### **4.1. Scanner to UI Communication**

1. A StockyTouch instance starts and establishes a WebSocket connection with the backend, identifying itself with a unique ui\_instance\_id.  
2. The UI displays a QR code containing {"command": "associate\_ui", "payload": "ui\_instance\_id"}.  
3. A user scans this QR code with a physical scanner.  
4. The backend receives this command and updates the scanner's user.details to include the associated\_ui\_id.  
5. Later, the user scans a UI command, e.g., {"command": "show\_view", "payload": "log"}.  
6. The backend identifies the scanner, retrieves its associated UI ID, and sends a command down the corresponding WebSocket.  
7. The StockyTouch instance receives the command and switches to the Log tab.

### **4.2. Data Deletion Rules**

* **Items:** An Item is never truly deleted. When its total quantity reaches zero, it is considered "hidden" and excluded from default views. It can be viewed in the "Zero Stock" filter. A permanent deletion option is available to Admins from this view.  
* **Locations:** A Location can only be deleted if it is empty. The UI is responsible for orchestrating a "move" workflow to empty the location before deletion.

### **4.3. Search Functionality**

The inventory search will be comprehensive, querying all fields on the Item model (name, description, upc, id). Location filtering is handled separately by a dedicated UI filter.