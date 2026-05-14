"""Authentication Pydantic schemas.

Defines the data structures used for JWT tokens and authentication flow.
"""

from pydantic import BaseModel


class Token(BaseModel):
    """OAuth2 Bearer Token response schema.

    Attributes:
        access_token: The generated JWT access token string.
        token_type: The type of the token, typically 'bearer'.

    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data schema.

    Data encoded inside the JWT token to identify the user.

    Attributes:
        username: The username extracted from the token subject payload.

    """

    email: str | None = None
