# Part 1 — Pattern Evidence Summary

| Pattern | File | Lines | Evidence |
|---------|------|-------|----------|
| Repository | backend/app/crud/data_products.py | 1-150 | DataProductRepository class with get/create/update/delete |
| Decorator | backend/app/core/security.py | 45-72 | @requires_permission decorator wrapping FastAPI endpoints |
| Strategy | backend/app/core/policy_engine.py | 1-100 | PolicyStrategy ABC with OwnerPolicy, RolePolicy implementations |
| Chain of Responsibility | backend/app/core/policy_engine.py | 100-150 | PolicyChain.evaluate() iterates handler chain |
| Observer | backend/app/workflow/pipeline.py | 30-80 | WorkflowEngine.notify() dispatches to registered observers |
| Template Method | backend/app/workflow/pipeline.py | 80-130 | ExperimentRunner.run() calls abstract validate/process/publish |
| Factory Method | backend/app/schemas/*.py | various | Pydantic schema classes with from_orm factory methods |
