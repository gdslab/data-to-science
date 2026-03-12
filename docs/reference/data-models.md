# Data Models

This page describes the SQLAlchemy models that define the D2S database schema. Models are located in `backend/app/models/`.

## Entity hierarchy

D2S organizes data in a hierarchical structure:

```
User
├── Team
│   └── TeamMember (role: Owner, Manager, Viewer)
└── Project
    ├── ProjectMember (role: Owner, Manager, Viewer)
    ├── Location (geographic boundary)
    ├── VectorLayer (GeoJSON / shapefile data)
    ├── Campaign (field data collection)
    └── Flight (UAV mission)
        ├── DataProduct (orthomosaic, DSM, point cloud)
        │   ├── DataProductMetadata
        │   └── FilePermission (public/private)
        └── RawData (unprocessed uploads)
```

## Core models

### Users and authentication

| Model | Table | Description |
|-------|-------|-------------|
| `User` | `user` | User accounts with profile information and approval status |
| `ApiKey` | `api_key` | API keys for programmatic access |
| `RefreshToken` | `refresh_token` | JWT refresh tokens |
| `SingleUseToken` | `single_use_token` | One-time-use tokens for email verification and password reset |

### Teams

| Model | Table | Description |
|-------|-------|-------------|
| `Team` | `team` | Organizational groups of users |
| `TeamMember` | `team_member` | Membership with role (Owner, Manager, Viewer) |

### Projects

| Model | Table | Description |
|-------|-------|-------------|
| `Project` | `project` | Primary organizational unit — contains flights, data, and members |
| `ProjectMember` | `project_member` | Project membership with role assignment |
| `ProjectLike` | `project_like` | User bookmarks for projects |
| `ProjectModule` | `project_module` | Enabled feature modules per project |

### Flights and data

| Model | Table | Description |
|-------|-------|-------------|
| `Flight` | `flight` | UAV mission records associated with a project |
| `DataProduct` | `data_product` | Processed outputs (COG, COPC) linked to flights |
| `DataProductMetadata` | `data_product_metadata` | Extended metadata for data products |
| `RawData` | `raw_data` | Unprocessed file uploads linked to flights |

### Geospatial

| Model | Table | Description |
|-------|-------|-------------|
| `Location` | `location` | Geographic boundaries (PostGIS geometry) for projects |
| `VectorLayer` | `vector_layer` | User-uploaded vector data (GeoJSON, shapefile) |

### Access control

| Model | Table | Description |
|-------|-------|-------------|
| `FilePermission` | `file_permission` | Public/private access flags for data products |

### Indoor projects

| Model | Table | Description |
|-------|-------|-------------|
| `IndoorProject` | `indoor_project` | Indoor (non-geospatial) project container |
| `IndoorProjectData` | `indoor_project_data` | Data files within indoor projects |

### Extensions and integrations

| Model | Table | Description |
|-------|-------|-------------|
| `Extension` | `extension` | Available platform extensions |
| `TeamExtension` | `team_extension` | Extensions enabled for a team |
| `UserExtension` | `user_extension` | Extensions enabled for a user |
| `BreedbaseConnection` | `breedbase_connection` | Breedbase integration credentials |
| `Campaign` | `campaign` | Field data collection campaigns |

### System

| Model | Table | Description |
|-------|-------|-------------|
| `Job` | `job` | Background task tracking records |
| `Upload` | `upload` | Upload session tracking |
| `ShortenedUrl` | `shortened_url` | Short URLs for sharing data products |
| `UserStyle` | `user_style` | User map styling preferences |
| `DiskUsageStats` | `disk_usage_stats` | Storage usage statistics |
