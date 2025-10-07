"""
Custom exceptions for the core layer.
"""


class CoreError(Exception):
    """Base exception for core layer errors."""
    pass


class TaskExecutionError(CoreError):
    """Raised when task execution fails."""
    pass


class PlanningError(CoreError):
    """Raised when task planning fails."""
    pass


class AmbiguityDetected(CoreError):
    """Raised when ambiguity is detected during task execution."""
    
    def __init__(self, context: dict, message: str = "Ambiguity detected"):
        self.context = context
        super().__init__(message)


class CircularDependencyError(CoreError):
    """Raised when circular dependency is detected in task graph."""
    pass


class ServiceNotFoundError(CoreError):
    """Raised when requested service is not found."""
    pass
