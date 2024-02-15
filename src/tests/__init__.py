from scripts.utils import generate_line_creds


INVALID_HOSTS = ["1.1.1.1.1.1", "40000000312", "not_hostname", "", "       ", "\t\n"]

# One user
RANDOM_VALID_CREDS = generate_line_creds(10)

# Two users
RANDOM_VALID_CREDS_2 = generate_line_creds(5, "d")

# One user
RANDOM_VALID_CREDS_3 = [generate_line_creds(3), generate_line_creds(6)]

# two users
RANDOM_VALID_CREDS_4 = [generate_line_creds(2, "d"), generate_line_creds(4, "d")]
