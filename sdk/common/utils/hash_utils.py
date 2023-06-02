import bcrypt


def hash_new_password(password: str) -> str:
    """
    Hash the provided password with a randomly-generated salt and return the
    salt and hash to store in the database.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(str.encode(password), salt)
    return hashed.decode()


def is_correct_password(pw_hash: str, password: str) -> bool:
    """
    Given a previously-stored salt and hash, and a password provided by a user
    trying to log in, check whether the password is correct.
    """

    both_exists = pw_hash and password
    if not both_exists:
        return False

    try:
        return bcrypt.checkpw(str.encode(password), str.encode(pw_hash))
    except ValueError:
        return False
