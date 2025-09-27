# Changelog

All notable changes to Stocky Backend will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-09-27

### Fixed
- **Authentication**: Fixed bcrypt compatibility issues with Python 3.13
  - Added proper handling for bcrypt's 72-byte password limit
  - Improved error handling in password hashing and verification
  - Enhanced UTF-8 encoding handling for international characters

## [0.2.0] - 2025-09-27 - The Shopping List Update

### Added
- **Shopping Lists Feature**: Complete collaborative shopping list management
  - Create, read, update, and delete shopping lists with public/private visibility
  - Collaborative editing: public lists editable by any authenticated user
  - Add, update, and remove items with quantity management
  - Duplicate shopping lists with all items
  - Complete audit logging with user attribution and JSON details
  - 10 new REST API endpoints under `/api/v1/shopping-lists/`
- **Database Schema**: 3 new tables (`shopping_lists`, `shopping_list_items`, `shopping_list_logs`)
- **Comprehensive Documentation**: Updated API reference and source code structure docs
- **Shopping Lists Design Document**: Complete feature specification and implementation guide

### Changed
- Updated API documentation to include shopping lists endpoints
- Enhanced source code structure documentation with shopping lists module

### Technical
- Multi-platform Docker support (linux/amd64, linux/arm64)
- Alembic migration `b4f781f67c01` for shopping lists schema
- Comprehensive Pydantic schemas for request/response validation
- Enhanced CRUD operations with collaborative access control

## [0.1.0] - 2025-09-20 - Initial Release

### Added
- **Core Inventory Management**: Complete home kitchen inventory system
- **User Management**: JWT and API key authentication with role-based access control
- **Item Catalog**: Product management with UPC support and external API integration
- **Location Management**: Storage location tracking (pantry, refrigerator, freezer, counter)
- **SKU/Inventory Tracking**: Item-location relationships with quantities and expiry dates
- **Barcode Scanner Integration**: Scanner device management and UPC lookups
- **System Logging**: Comprehensive application logging and audit trails
- **Alert System**: Low stock and expiry date notifications
- **Backup & Restore**: Full database backup and restore capabilities (admin-only)
- **RESTful API**: 37 endpoints across 9 modules with comprehensive OpenAPI documentation
- **Database**: SQLite with SQLAlchemy ORM and Alembic migrations
- **Docker Support**: Production-ready containerization
- **Comprehensive Testing**: Unit, integration, API, and end-to-end test suites

### Technical
- FastAPI framework with async support
- Pydantic v2 for data validation and settings management
- JWT token authentication with refresh token support
- Role-based authorization (ADMIN, MEMBER roles)
- CORS configuration for web frontend integration
- Environment-based configuration management
- Multi-architecture Docker builds

---

## Release Notes

### Version 0.2.0 - The Shopping List Update
This major update introduces collaborative shopping lists, enabling users to create shared shopping lists that can be edited by multiple users. The feature includes complete audit logging, making it perfect for family or household shopping coordination.

### Version 0.1.0 - Initial Release  
The foundational release of Stocky Backend, providing a complete home kitchen inventory management system with barcode scanning, location tracking, and comprehensive API for frontend integration.