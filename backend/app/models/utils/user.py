from fastapi import HTTPException, status
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime


class utcnow(expression.FunctionElement):
    type = DateTime()
    inherit_cache = True


class utcexpire(expression.FunctionElement):
    # used to set default datetime 1 week from current datetime
    type = DateTime()
    inherit_cache = True


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


@compiles(utcexpire, "postgresql")
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP + INTERVAL '7 DAYS')"


def more_than_two_repeating_chars_in_a_row(chars: str):
    count = 0
    prev_char = None
    for char in chars:
        # increment if current char matches previous char
        if char == prev_char or char is None:
            count += 1
        else:
            # reset count to 0
            count = 1

        # return False if count passes 2 repeating chars
        if count > 2:
            return True

        prev_char = char

    return False


def validate_password(pwd: str):
    # cannot repeat more than two characters in a row
    if more_than_two_repeating_chars_in_a_row(pwd):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password cannot have more than two repeating characters in a row",
        )
