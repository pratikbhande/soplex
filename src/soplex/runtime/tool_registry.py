"""
Tool registry for soplex.
Manages registration and execution of tool functions.
"""
import yaml
import time
from typing import Dict, Any, Callable, Optional, Union, List
from pathlib import Path
import inspect
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    """Definition of a tool function."""
    name: str
    function: Callable
    description: str
    parameters: Dict[str, Any]
    mock_response: Optional[Any] = None
    is_mock: bool = False


class ToolRegistry:
    """
    Registry for managing tool functions.
    Supports both real tools and mock tools for testing.
    """

    def __init__(self):
        """Initialize empty tool registry."""
        self.tools: Dict[str, ToolDefinition] = {}
        self.mock_mode = False

    def register_tool(
        self,
        name: str,
        function: Callable,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        mock_response: Optional[Any] = None
    ) -> None:
        """
        Register a tool function.

        Args:
            name: Tool identifier
            function: Callable function
            description: Description of what the tool does
            parameters: Parameter schema (JSON Schema style)
            mock_response: Mock response for testing
        """
        if parameters is None:
            # Try to extract parameters from function signature
            parameters = self._extract_parameters_from_function(function)

        tool_def = ToolDefinition(
            name=name,
            function=function,
            description=description,
            parameters=parameters,
            mock_response=mock_response,
            is_mock=False
        )

        self.tools[name] = tool_def

    def register_mock_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        mock_response: Any
    ) -> None:
        """
        Register a mock tool for testing.

        Args:
            name: Tool identifier
            description: Tool description
            parameters: Parameter schema
            mock_response: Response to return when called
        """
        def mock_function(**kwargs):
            """Mock function that returns predefined response."""
            return mock_response

        tool_def = ToolDefinition(
            name=name,
            function=mock_function,
            description=description,
            parameters=parameters,
            mock_response=mock_response,
            is_mock=True
        )

        self.tools[name] = tool_def

    def load_tools_from_yaml(self, yaml_path: Union[str, Path]) -> None:
        """
        Load mock tools from YAML configuration.

        Args:
            yaml_path: Path to YAML file with tool definitions
        """
        yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            raise FileNotFoundError(f"Tools YAML file not found: {yaml_path}")

        with open(yaml_path) as f:
            tools_data = yaml.safe_load(f)

        for tool_name, tool_config in tools_data.items():
            self.register_mock_tool(
                name=tool_name,
                description=tool_config.get("description", ""),
                parameters=tool_config.get("parameters", {}),
                mock_response=tool_config.get("mock_responses", {})
            )

    def call_tool(self, name: str, **kwargs) -> Any:
        """
        Call a registered tool.

        Args:
            name: Tool name
            **kwargs: Parameters to pass to the tool

        Returns:
            Tool result

        Raises:
            ValueError: If tool not found
            RuntimeError: If tool call fails
        """
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found in registry")

        tool = self.tools[name]

        try:
            # Handle mock tools with multiple responses
            if tool.is_mock and isinstance(tool.mock_response, dict):
                # Use 'default' response if no specific response specified
                response_key = kwargs.get('_response_type', 'default')
                if response_key in tool.mock_response:
                    return tool.mock_response[response_key]
                elif 'default' in tool.mock_response:
                    return tool.mock_response['default']
                else:
                    # Return first available response
                    return next(iter(tool.mock_response.values()))

            # Call the actual function
            return tool.function(**kwargs)

        except Exception as e:
            raise RuntimeError(f"Tool '{name}' failed: {e}")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        return self.tools.get(name)

    def get_tool_names(self) -> List[str]:
        """Get list of registered tool names."""
        return list(self.tools.keys())

    def get_tools_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered tools."""
        return {
            name: {
                "description": tool.description,
                "parameters": tool.parameters,
                "is_mock": tool.is_mock,
                "has_mock_response": tool.mock_response is not None,
            }
            for name, tool in self.tools.items()
        }

    def set_mock_mode(self, enabled: bool) -> None:
        """Enable or disable mock mode."""
        self.mock_mode = enabled

    def is_tool_available(self, name: str) -> bool:
        """Check if a tool is available."""
        return name in self.tools

    def validate_tool_call(self, name: str, parameters: Dict[str, Any]) -> bool:
        """
        Validate parameters for a tool call.

        Args:
            name: Tool name
            parameters: Parameters to validate

        Returns:
            True if parameters are valid
        """
        if name not in self.tools:
            return False

        tool = self.tools[name]

        # Basic validation - check required parameters exist
        required_params = []
        if 'properties' in tool.parameters:
            for param_name, param_def in tool.parameters['properties'].items():
                if param_def.get('required', False):
                    required_params.append(param_name)

        # Check all required parameters are provided
        for param in required_params:
            if param not in parameters:
                return False

        return True

    def clear(self) -> None:
        """Clear all registered tools."""
        self.tools.clear()

    def _extract_parameters_from_function(self, function: Callable) -> Dict[str, Any]:
        """
        Extract parameter schema from function signature.

        Args:
            function: Function to analyze

        Returns:
            JSON Schema-style parameter definition
        """
        sig = inspect.signature(function)
        properties = {}

        for param_name, param in sig.parameters.items():
            if param_name == "kwargs":
                continue

            param_def = {"type": "string"}  # Default type

            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_def["type"] = "integer"
                elif param.annotation == float:
                    param_def["type"] = "number"
                elif param.annotation == bool:
                    param_def["type"] = "boolean"
                elif param.annotation == list:
                    param_def["type"] = "array"
                elif param.annotation == dict:
                    param_def["type"] = "object"

            # Check if parameter has default value
            if param.default != inspect.Parameter.empty:
                param_def["default"] = param.default
            else:
                param_def["required"] = True

            properties[param_name] = param_def

        return {
            "type": "object",
            "properties": properties
        }


# Global registry instance
default_registry = ToolRegistry()


# Convenience functions

def register_tool(
    name: str,
    function: Callable,
    description: str = "",
    parameters: Optional[Dict[str, Any]] = None,
    mock_response: Optional[Any] = None
) -> None:
    """Register a tool in the default registry."""
    default_registry.register_tool(name, function, description, parameters, mock_response)


def call_tool(name: str, **kwargs) -> Any:
    """Call a tool from the default registry."""
    return default_registry.call_tool(name, **kwargs)


def load_mock_tools(yaml_path: Union[str, Path]) -> None:
    """Load mock tools from YAML into default registry."""
    default_registry.load_tools_from_yaml(yaml_path)


def get_registry() -> ToolRegistry:
    """Get the default tool registry."""
    return default_registry


# Common tool functions for testing

def mock_database_lookup(table: str, query: Dict[str, Any]) -> Dict[str, Any]:
    """Mock database lookup tool."""
    return {
        "status": "success",
        "table": table,
        "query": query,
        "results": [{"id": 1, "data": "mock_data"}],
        "count": 1
    }


def mock_api_call(endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Mock API call tool."""
    return {
        "status": "success",
        "endpoint": endpoint,
        "method": method,
        "data": data,
        "response": {"result": "success", "mock": True},
        "status_code": 200
    }


def mock_email_sender(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Mock email sending tool."""
    return {
        "status": "sent",
        "to": to,
        "subject": subject,
        "message_id": f"mock_{int(time.time())}",
        "delivery_time": "immediate"
    }


# Register common mock tools
register_tool("mock_database_lookup", mock_database_lookup, "Mock database lookup")
register_tool("mock_api_call", mock_api_call, "Mock API call")
register_tool("mock_email_sender", mock_email_sender, "Mock email sender")