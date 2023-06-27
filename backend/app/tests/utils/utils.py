from datetime import datetime

from faker import Faker


faker = Faker()


def random_email() -> str:
    """Create random email address."""
    return faker.email()


def random_full_name() -> dict[str, str]:
    """Create random first and last name."""
    return {"first": faker.first_name(), "last": faker.last_name()}


def random_group_name() -> str:
    """Create random group name."""
    return faker.company()


def random_group_description() -> str:
    """Create random group description."""
    return faker.sentence()


def random_password() -> str:
    """Create random password."""
    return faker.password()
