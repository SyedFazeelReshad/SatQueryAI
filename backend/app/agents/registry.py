from pydantic import BaseModel
from pathlib import Path
import yaml

from typing import Union

class ToolDefinition(BaseModel):
    id: str = ""
    name: str
    version: str = "1.0"
    type: str = "general"
    description: str = ""
    supported_tasks: list[str] = []
    supported_modalities: list[str] = []
    output: Union[list[str], str] = []
    parameters: dict = {}

class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, ToolDefinition] = {}

    def load_from_yaml(self, path: Path) -> None:
        if not path.exists():
            return
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
            raw_tools = data.get('tools', {})
            if isinstance(raw_tools, dict):
                for tool_id, tool_data in raw_tools.items():
                    if isinstance(tool_data, dict):
                        t_data = dict(tool_data)
                        t_data['id'] = tool_id
                        tool = ToolDefinition(**t_data)
                        self.tools[tool_id] = tool
                        self.tools[tool.name] = tool
            elif isinstance(raw_tools, list):
                for tool_data in raw_tools:
                    if isinstance(tool_data, dict):
                        tool = ToolDefinition(**tool_data)
                        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> ToolDefinition | None:
        return self.tools.get(name)

    def get_tools_for_task(self, task: str) -> list[ToolDefinition]:
        return [t for t in self.tools.values() if task in t.supported_tasks]

    def list_tools(self) -> list[str]:
        return list(self.tools.keys())

tool_registry = ToolRegistry()
