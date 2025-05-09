"""
Tool Utilities

This module provides utility functions and type definitions for tools.
"""

from typing import TypedDict, Dict, List, Any, Optional, Union, Literal

# Success response type
class SuccessResponse(TypedDict):
    success: Literal[True]
    # Add any common success fields here

# Error response type
class ErrorResponse(TypedDict):
    success: Literal[False]
    error: str
    traceback: Optional[str]

# Union type for tool responses
ToolResponse = Union[SuccessResponse, ErrorResponse]

# Helper function to create success response
def success_response(**kwargs) -> SuccessResponse:
    """Create a standardized success response."""
    response: Dict[str, Any] = {"success": True}
    response.update(kwargs)
    return response

# Helper function to create error response
def error_response(error_message: str, traceback: Optional[str] = None) -> ErrorResponse:
    """Create a standardized error response."""
    response: Dict[str, Any] = {"success": False, "error": error_message}
    if traceback:
        response["traceback"] = traceback
    return response