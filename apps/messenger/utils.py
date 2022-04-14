import hashlib
import random
from datetime import datetime


class AuthenticationCredentials:
    hashed_auth_token = ''
    salt = ''

    def __init__(self, auth_token, salt=None):
        if salt:
            self.salt = salt
        else:
            self.salt = random.randint(100000, 999999).__str__()
        self.hashed_auth_token = self.get_hash_value(auth_token)

    def get_hash_value(self, auth_token):
        hash_obj = hashlib.sha1()
        hash_obj.update(str(auth_token + self.salt).encode('utf-8'))
        return hash_obj.hexdigest()

    def verify(self, auth_token):
        value = self.get_hash_value(auth_token)
        return value.__eq__(self.hashed_auth_token)


def validate_date_str(date_text):
    try:
        return datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")
