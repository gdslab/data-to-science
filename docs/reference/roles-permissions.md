# Roles and Permissions

This document summarizes what each role can do across the D2S platform. For the design rationale behind this system, see [Authentication and Authorization](../explanation/authentication.md).

## Role hierarchy

The platform uses a three-tier role hierarchy for both **Team Members** and **Project Members**:

| Role | Level | Description |
|------|-------|-------------|
| **Owner** | 3 (highest) | Full control including delete operations |
| **Manager** | 2 | Read and write access, but cannot delete |
| **Viewer** | 1 (lowest) | Read-only access |

---

## Team permissions

Teams are used to organize users and can be associated with projects.

### Team operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| Create team | Any approved user | Any approved user | Any approved user |
| View team details | Yes | Yes | Yes |
| List teams user belongs to | Yes | Yes | Yes |
| Update team | Yes | No | No |
| Delete team | Yes | No | No |

### Team member management

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| List team members | Yes | Yes | Yes |
| Add team member | Yes | No | No |
| Add multiple team members | Yes | No | No |
| Update team member role | Yes | Yes* | No |
| Remove team member | Yes | No | No |

*\*Managers can update roles but **cannot** modify owners or promote members to owner.*

**Special restrictions:**

- The team creator (original owner) cannot be modified or removed
- Demo users cannot perform write/delete operations on teams

---

## Project permissions

Projects are the primary organizational unit containing flights, data products, and other resources.

### Project operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| Create project | Any approved user | Any approved user | Any approved user |
| View project | Yes | Yes | Yes |
| List user's projects | Yes | Yes | Yes |
| Update project | Yes | Yes | No |
| Deactivate (delete) project | Yes | No | No |
| Bookmark/unbookmark project | Yes | Yes | Yes |

### Project member management

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| List project members | Yes | Yes | Yes |
| View project member | Yes | Yes | Yes |
| Add project member | Yes | No | No |
| Add multiple project members | Yes | No | No |
| Update project member role | Yes | No | No |
| Remove project member | Yes | No | No |

**Special restrictions:**

- The project creator (original owner) cannot be removed
- Demo users cannot perform write/delete operations on projects

---

## Flight permissions

Flights belong to projects and contain raw data and data products.

### Flight operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| Create flight | Yes | Yes | No |
| View flight | Yes | Yes | Yes |
| List flights in project | Yes | Yes | Yes |
| Update flight | Yes | Yes | No |
| Move flight to another project | Yes* | No | No |
| Deactivate (delete) flight | Yes | Yes** | No |
| Check flight processing progress | Yes | Yes | No |

*\*User must be Owner of both source and destination projects.*

*\*\*Flight deletion requires `can_read_write_flight` AND `can_read_write_delete_project` — effectively requiring Manager+ on flight and Owner on project.*

**Additional restriction:**

- Flights cannot be deactivated when the project is published to a STAC catalog

---

## Data product permissions

Data products are derived outputs (GeoTIFFs, point clouds, etc.) associated with flights.

### Data product operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| View data product | Yes | Yes | Yes |
| List data products | Yes | Yes | Yes |
| Update data product bands | Yes | Yes | No |
| Update data product type | Yes | Yes | No |
| Deactivate (delete) data product | Yes | No | No |
| Generate shortened URL | Yes | Yes | Yes |
| Run processing tools (NDVI, CHM, etc.) | Yes | Yes | No |
| Calculate zonal statistics | Yes | Yes | Yes |

**Additional restrictions:**

- Data products cannot be deactivated when the project is published to a STAC catalog
- Point cloud and panoramic data types cannot be changed

---

## Raw data permissions

Raw data represents unprocessed uploads associated with flights.

### Raw data operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| View raw data | Yes | Yes | Yes |
| Download raw data | Yes | Yes | Yes |
| List raw data | Yes | Yes | Yes |
| Deactivate (delete) raw data | Yes | No | No |
| Process raw data | Yes | Yes | No |
| Check processing progress | Yes | Yes | No |

---

## Vector layer permissions

Vector layers are GeoJSON/shapefile data associated with projects.

### Vector layer operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| Upload vector layer | Yes | Yes | No |
| Create from GeoJSON | Yes | Yes | No |
| View vector layer | Yes | Yes | Yes |
| List vector layers | Yes | Yes | Yes |
| Download vector layer | Yes | Yes | Yes |
| Update vector layer name | Yes | Yes | No |
| Delete vector layer | Yes | Yes | No |

---

## Campaign (field data) permissions

Campaigns are field data collection configurations within projects.

### Campaign operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| Create campaign | Yes | Yes | No |
| View campaign | Yes | Yes | Yes |
| Update campaign | Yes | Yes | No |
| Deactivate campaign | Yes | No | No |
| Download campaign template | Yes | Yes | Yes |

---

## Location permissions

Locations are geographic boundaries within projects.

### Location operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| View location | Yes | Yes | Yes |
| Update location | Yes | Yes | No |
| Upload project boundary | Any approved user | Any approved user | Any approved user |
| Upload vector layer shapefile | Any approved user | Any approved user | Any approved user |

---

## STAC catalog permissions

STAC (SpatioTemporal Asset Catalog) operations for publishing project data.

### STAC operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| View cached STAC metadata | Yes | No | No |
| Generate STAC preview | Yes | No | No |
| Publish to STAC catalog | Yes | No | No |
| Remove from STAC catalog | Yes | No | No |
| View STAC metadata (published) | Yes | No | No |

---

## File permission management

Controls public visibility of data products.

### File permission operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| Update file permission (public/private) | Yes | No | No |

**Additional restriction:**

- Files cannot be made private when the project is published to a STAC catalog

---

## Indoor project permissions

Indoor projects are separate from regular projects and have their own permission system.

### Indoor project operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| Create indoor project | Any approved user | Any approved user | Any approved user |
| View indoor project | Yes | Yes | Yes |
| List indoor projects | Yes | Yes | Yes |
| Update indoor project | Yes | Yes | No |
| Deactivate indoor project | Yes | No | No |

### Indoor project member management

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| List project members | Yes | Yes | Yes |
| View project member | Yes | Yes | Yes |
| Add project member | Yes | No | No |
| Add multiple project members | Yes | No | No |
| Update project member role | Yes | No | No |
| Remove project member | Yes | No | No |

### Indoor project data operations

| Action | Owner | Manager | Viewer |
|--------|:-----:|:-------:|:------:|
| List project data files | Yes | Yes | Yes |
| View spreadsheet data | Yes | Yes | Yes |
| View plant data | Yes | Yes | Yes |
| View visualization data | Yes | Yes | Yes |

**Special restrictions:**

- Demo users cannot create indoor projects
- The indoor project creator cannot be removed as a member

---

## Admin permissions

Admin users (superusers) have special elevated privileges.

### Admin-only operations

| Action | Regular User | Admin |
|--------|:------------:|:-----:|
| View all users (including unapproved) | No | Yes |
| Update user approval status | No | Yes |
| View site statistics | No | Yes |
| View project data usage statistics | No | Yes |
| View/manage extensions | No | Yes |
| Update team extensions | No | Yes |
| Update user extensions | No | Yes |

---

## Demo user restrictions

Demo users have special restrictions that prevent modifications:

| Restriction |
|------------|
| Cannot create teams |
| Cannot modify teams (write/delete) |
| Cannot create projects |
| Cannot modify projects (write/delete) |
| Cannot create indoor projects |
| Cannot update project member roles for demo users |

---

## API key authentication

Some endpoints support authentication via API key in addition to JWT tokens:

| Endpoint | JWT | API Key |
|----------|:---:|:-------:|
| Read project | Yes | Yes |
| List flights | Yes | Yes |
| List vector layers | Yes | Yes |
| Download vector layer | Yes | Yes |

---

## Permission inheritance

When a project is created with a team:

- All team members are automatically added as project members
- Team member roles are inherited as project member roles
- Owner of team becomes Owner of project members

---

## Dependency functions reference

The following dependency functions control access in the API:

### User authentication

- `get_current_user` — Validates JWT token
- `get_current_approved_user` — User must be approved and email confirmed
- `get_current_admin_user` — User must be superuser
- `get_current_approved_user_by_jwt_or_api_key` — Accepts JWT or API key
- `get_optional_current_user` — Returns None if auth fails (no error)

### Team permissions

- `can_read_team` — Any team member
- `can_read_write_team` — Manager or Owner
- `can_read_write_delete_team` — Owner only

### Project permissions

- `can_read_project` — Viewer, Manager, or Owner
- `can_read_write_project` — Manager or Owner
- `can_read_write_delete_project` — Owner only
- `can_read_project_with_jwt_or_api_key` — Read access via JWT or API key
- `can_read_write_project_with_jwt_or_api_key` — Write access via JWT or API key

### Flight permissions

- `can_read_flight` — Viewer, Manager, or Owner
- `can_read_write_flight` — Manager or Owner
- `can_read_write_delete_flight` — Owner only

### Indoor project permissions

- `can_read_indoor_project` — Viewer, Manager, or Owner
- `can_read_write_indoor_project` — Manager or Owner
- `can_read_write_delete_indoor_project` — Owner only
