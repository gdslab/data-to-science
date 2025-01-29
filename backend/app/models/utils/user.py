from fastapi import HTTPException, status


def more_than_two_repeating_chars_in_a_row(chars: str) -> bool:
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


def validate_password(pwd: str) -> None:
    # cannot repeat more than two characters in a row
    if more_than_two_repeating_chars_in_a_row(pwd):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password cannot have more than two repeating characters in a row",
        )
