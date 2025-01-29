from typing import Any

from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime


class utcnow(expression.FunctionElement):
    type: DateTime = DateTime()
    inherit_cache: bool = True


@compiles(utcnow, "postgresql")
def pg_utcnow(element: utcnow, compiler: Any, **kw: Any) -> str:
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"
