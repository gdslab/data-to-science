from typing import Any

from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime


class utcexpire(expression.FunctionElement):
    type: DateTime = DateTime()
    inherit_cache: bool = True


@compiles(utcexpire, "postgresql")
def pg_utcexpire(element: utcexpire, compiler: Any, **kw: Any) -> str:
    return "TIMEZONE('utc', CURRENT_TIMESTAMP + INTERVAL '7 DAYS')"
