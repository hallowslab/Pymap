from typing import List
from random import choice, choices, randint
import string


def generate_email(domain: str) -> str:
    """
    Generate a random email address with a specified domain.
    The address will consist of random letters and digits between 6 to 10 characters

    Args:
        domain (str): The domain name for the email address.

    Returns:
        str: A randomly generated email address with the specified domain.

    Example:
        >>> generate_email("example.com")
        'abc123@example.com'
    """
    # Choose a random length for the email address
    email_length = randint(6, 10)

    # Generate a random email address
    email = "".join(choices(string.ascii_lowercase + string.digits, k=email_length))
    email = email + "@" + domain

    return email


def generate_password() -> str:
    """
    Generate a random password consisting of letters, digits, and special characters
    (#()!) with a length between 8 and 20 characters.

    Returns:
        str: A randomly generated password.

    Example:
        >>> generate_password()
        '7h@B3#2C!1kGh(0D&'
    """
    # Generate a random password
    length = randint(8, 20)
    password = "".join(choices(string.ascii_letters + string.digits + "#()!", k=length))

    return password


# s for single d for double
def generate_line_creds(
    count: int, creds_type: str = "s", domains: List[str] = ["example.com"]
) -> List[str]:
    """
    Generate a list of credential strings based on the specified count, credentials type, and domains.

    Args:
        count (int): The number of credential strings to generate.
        creds_type (str, optional): The type of credentials to generate. Use 's' for single credentials (email and password pair), 'd' for double credentials (two email and password pairs).
        domains (List[str], optional): A list of domain names to use for generating email addresses. Defaults to ["example.com"].

    Returns:
        List[str]: A list of credential strings. Each string represents an account and respective password, separated by a space.

    Example:
        >>> generate_line_creds(3)
        ['abc123@example.com 7h@B3#2C!1kGh(0D&', 'def456@example.com 8g@F4$3d#9QwRtY*', 'ghi789@example.com 2p@Z1%qR7LmN9oP#']
        >>> generate_line_creds(2,"d")
        ['abc123@example.com 7h@B3#2C!1kGh(0D& def456@example.com 8g@F4$3d#9QwRtY*', 'ghi789@example.com 2p@Z1%qR7LmN9oP# jkl098@example.com 6j@G8^5t']
    """
    creds: List[str] = []
    for _ in range(count):
        new_string = (
            f"{generate_email(choice(domains))} {generate_password()}"
            if creds_type == "s"
            else f"{generate_email(choice(domains))} {generate_password()} {generate_email(choice(domains))} {generate_password()}"
        )
        creds.append(new_string)
    return creds
