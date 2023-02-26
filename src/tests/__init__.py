import random
import string
from typing import List, Tuple


def generate_email() -> str:
    # Choose a random length for the email address
    email_length: int = random.randint(6, 10)

    # Generate a random email address
    email: str = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=email_length)
    )
    email = email + "@example.com"

    return email


def generate_password() -> str:
    # Generate a random password
    length: int = random.randint(8, 20)
    password: str = "".join(
        random.choices(string.ascii_letters + string.digits + "#()!", k=length)
    )

    return password


# s for single d for double
def generate_line_creds(count: int, creds_type: str = "s") -> Tuple[List[str], ...]:
    creds: List[List[str]] = []
    for _ in range(count):
        if creds_type == "s":
            new_creds = [generate_email(), generate_password()]
        else:
            new_creds = [generate_email(), generate_password(), generate_email(), generate_password()]
        creds.append(new_creds)
    return tuple(creds)


INVALID_HOSTS: List[str] = ["1.1.1.1.1.1", "40000000312", "not_hostname", "", "       ", "\t\n"]

# One user
RANDOM_VALID_CREDS: Tuple[List[str], ...] = generate_line_creds(5)

# Two users
RANDOM_VALID_CREDS_2: Tuple[List[str], ...] = generate_line_creds(5, "d")

# One user
RANDOM_VALID_CREDS_3: Tuple[List[str], ...] = generate_line_creds(5)

# two users
RANDOM_VALID_CREDS_4: Tuple[List[str], ...] = generate_line_creds(5, "d")
