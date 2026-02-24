import os
import json
from typing import Dict
from formula_to_tool import FormulaTool


class ToolRegistry:

    def __init__(self):
        self.tools: Dict[str, FormulaTool] = {}

    def register(self, tool: FormulaTool):
        if tool.name in self.tools:
            print(f"[WARN] Tool {tool.name} overwritten")
        self.tools[tool.name] = tool

    def get(self, name: str):
        return self.tools.get(name)

    def list_tools(self):
        return list(self.tools.keys())

    def load_from_directory(self, directory: str):
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                path = os.path.join(directory, filename)
                with open(path, "r", encoding="utf-8") as f:
                    spec = json.load(f)

                tool = FormulaTool(spec)
                self.register(tool)

        print(f"[INFO] Loaded {len(self.tools)} tools.")
