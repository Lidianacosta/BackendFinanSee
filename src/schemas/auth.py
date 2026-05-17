"""Authentication Pydantic schemas.

Defines the data structures used for JWT tokens and authentication flow.
"""

from pydantic import BaseModel, EmailStr, Field, model_validator


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


class ForgotPasswordIn(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr


class ResetPasswordIn(BaseModel):
    """Schema for reset password request."""

    token: str
    new_password: str = Field(min_length=8)
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> "ResetPasswordIn":
        """Ensure new_password and confirm_password match."""
        if self.new_password != self.confirm_password:
            raise ValueError("As senhas não coincidem")
        return self
