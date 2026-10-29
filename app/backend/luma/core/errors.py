class DomainError(Exception):
    """A safe, caller-visible business rejection with an explicit HTTP status; never include provider secrets."""

    def __init__(self, message: str, status: int = 409):
        """Store a safe business error message and its response status for the API boundary."""
        self.message = message
        self.status = status
