from dataclasses import dataclass
import logging
from os import environ

# Get current logger
log = logging.getLogger(__name__)

class AuthError(Exception):
    pass

class SecretString:
    """
    Conceals a string (mainly used for passwords n such)
    """
    def __init__(self, secret: str) -> None:
        """
        Init with secret string
        """
        self._secret = secret
    
    def __repr__(self):
        """
        Just return asterisks
        """
        return "'" + "*"*len(self._secret) + "'"
    
    def reveal(self):
        """
        Return the actual string
        """
        return self._secret
    
@dataclass
class User:
    """
    Represent log in user
    """
    username: str
    password: SecretString

    @classmethod
    def from_env(cls):
        """
        Load user from environment variable
        """
        log.info("Get user from environment")
        try:
            username = environ['MH_USERNAME']
            password = SecretString(environ['MH_PASSWORD'])
        except KeyError as e:
            raise AuthError("It looks like your username or password isn't defined. Please set these by setting the MH_USERNAME and MH_PASSWORD environment variables respectively.") from e
        user = cls(username=username, password=password)
        log.info("Found user: %s", user)
        return user