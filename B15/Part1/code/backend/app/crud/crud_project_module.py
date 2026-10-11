from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.module_type import ModuleType
from app.models.project_module import ProjectModule
from app.schemas.project_module import ProjectModuleCreate, ProjectModuleUpdate


class CRUDProjectModule(
    CRUDBase[ProjectModule, ProjectModuleCreate, ProjectModuleUpdate]
):
    def get_project_modules_by_project_id(
        self, db: Session, project_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Return all module types with their enabled status for a given project.
        Required modules are always returned as enabled (or treated as enabled if missing).
        """
        statement = (
            select(
                ModuleType.module_name,
                ModuleType.label,
                ModuleType.description,
                ModuleType.required,
                ModuleType.sort_order,
                ProjectModule.enabled,
                ProjectModule.id,
            )
            .outerjoin(
                ProjectModule,
                (ProjectModule.module_name == ModuleType.module_name)
                & (ProjectModule.project_id == project_id),
            )
            .order_by(ModuleType.sort_order)
        )

        with db as session:
            result = session.execute(statement).all()

            return [
                {
                    "id": row.id
                    or UUID(int=0),  # Use a default UUID if no record exists
                    "project_id": project_id,
                    "module_name": row.module_name,
                    "label": row.label,
                    "description": row.description,
                    "required": row.required,
                    "enabled": row.required or row.enabled is True,
                    "sort_order": row.sort_order,
                }
                for row in result
            ]

    def update_project_module(
        self, db: Session, project_id: UUID, module_name: str, enabled: bool
    ) -> Optional[ProjectModule]:
        """
        Update the enabled status of a project module.
        """
        with db as session:
            project_module = (
                session.query(ProjectModule)
                .filter(
                    ProjectModule.project_id == project_id,
                    ProjectModule.module_name == module_name,
                )
                .first()
            )
            if not project_module:
                return None

            project_module.enabled = enabled
            session.commit()
            session.refresh(project_module)

            return project_module


project_module = CRUDProjectModule(ProjectModule)
