from typing import Literal

from pydantic import Field

from luma.core.contracts import StrictModel


class Ownership(StrictModel):
    """Versioned staff command to pause automation or explicitly return a conversation to the agent."""

    expected_version: int = Field(ge=1)
    owner: Literal["agent", "staff"]


class TextInput(StrictModel):
    """Bounded plain-text input with undeclared fields rejected at the API boundary."""

    text: str = Field(min_length=1, max_length=8000)


class Intake(TextInput):
    """Local-test request input; the API determines company, channel, recipient identity, and authority."""

    customer_name: str = Field(min_length=1, max_length=120)
    customer_company: str = Field(default="", max_length=160)


class StaffReply(TextInput):
    """A bounded human reply tied to the staff-owned conversation version, never a quotation approval command."""

    text: str = Field(min_length=1, max_length=2000)
    expected_version: int = Field(ge=1, strict=True)
