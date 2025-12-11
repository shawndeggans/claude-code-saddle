"""
{{EXPERT_NAME}} Expert MCP Server

An MCP server that wraps an LLM with domain-specific knowledge
to provide expert guidance for {{DOMAIN_DESCRIPTION}}.
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import yaml
from anthropic import Anthropic
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server instance
server = Server("{{expert_name}}-expert")

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.yaml"
EXPERT_ROOT = Path(__file__).parent.parent


def load_config() -> dict:
    """Load expert configuration from YAML file."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def load_knowledge(config: dict) -> str:
    """Load knowledge files into a single context string."""
    knowledge_parts = []

    # Load core files (always loaded)
    for pattern in config["knowledge"]["core_files"]:
        for path in EXPERT_ROOT.glob(pattern):
            if path.is_file():
                knowledge_parts.append(f"# {path.name}\n\n{path.read_text()}")

    # Load org patterns
    for pattern in config["knowledge"].get("org_patterns", []):
        for path in EXPERT_ROOT.glob(pattern):
            if path.is_file():
                knowledge_parts.append(f"# {path.name}\n\n{path.read_text()}")

    return "\n\n---\n\n".join(knowledge_parts)


# Response models
@dataclass
class ConsultResponse:
    """Response from consulting the expert."""
    answer: str
    confidence: Literal["high", "medium", "low"]
    references: list[str]
    follow_up_questions: list[str]
    outside_domain: bool = False


@dataclass
class ExecuteResponse:
    """Response from executing an action."""
    status: Literal["success", "failed", "needs_confirmation"]
    result: Optional[str] = None
    error: Optional[str] = None
    next_steps: list[str] = None

    def __post_init__(self):
        if self.next_steps is None:
            self.next_steps = []


@dataclass
class Issue:
    """An issue found during review."""
    severity: Literal["error", "warning", "info"]
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ReviewResponse:
    """Response from reviewing an artifact."""
    assessment: Literal["approved", "concerns", "rejected"]
    issues: list[Issue]
    suggestions: list[str]


@dataclass
class Fix:
    """A suggested fix for troubleshooting."""
    description: str
    steps: list[str]
    confidence: Literal["high", "medium", "low"]


@dataclass
class TroubleshootResponse:
    """Response from troubleshooting an error."""
    diagnosis: str
    root_cause: Optional[str]
    suggested_fixes: list[Fix]
    confidence: Literal["high", "medium", "low"]


class ExpertLLM:
    """Wrapper for LLM with expert knowledge context."""

    def __init__(self, config: dict):
        self.config = config
        self.client = Anthropic()
        self.knowledge = load_knowledge(config)
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt with knowledge context."""
        return f"""You are the {self.config['expert']['name']} expert.
Domain: {self.config['expert']['domain']}

You provide accurate, actionable guidance based on the following knowledge:

{self.knowledge}

Response Guidelines:
1. Be specific and actionable
2. Include code/config examples when relevant
3. State your confidence level (high/medium/low)
4. If a question is outside your domain, say so clearly
5. Reference specific knowledge sources when applicable

Boundaries:
{json.dumps(self.config.get('boundaries', {}), indent=2)}

If asked about something outside your domain, respond with outside_domain=true."""

    def query(self, prompt: str, response_format: str) -> str:
        """Query the LLM with the expert context."""
        message = self.client.messages.create(
            model=self.config["llm"]["model"],
            max_tokens=self.config["llm"]["max_tokens"],
            temperature=self.config["llm"]["temperature"],
            system=self.system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\nRespond with valid JSON matching this format:\n{response_format}"
                }
            ]
        )
        return message.content[0].text


def log_decision(query: str, response: dict, config: dict):
    """Log significant decisions for future reference."""
    log_dir = EXPERT_ROOT / config["logging"]["decision_log"]
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_file = log_dir / f"{timestamp}-decision.md"

    content = f"""# Decision Log Entry

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Query**: {query}

## Response

```json
{json.dumps(response, indent=2)}
```
"""
    log_file.write_text(content)
    logger.info(f"Decision logged to {log_file}")


# Initialize expert
config = load_config()
expert_llm = ExpertLLM(config)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available expert tools."""
    return [
        Tool(
            name="consult",
            description="Ask the expert a question about the domain",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question to ask the expert"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context for the question"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="execute",
            description="Have the expert perform a domain-specific action",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The action to perform"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters for the action"
                    }
                },
                "required": ["action", "parameters"]
            }
        ),
        Tool(
            name="review",
            description="Have the expert review a configuration, script, or plan",
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact": {
                        "type": "string",
                        "description": "The content to review"
                    },
                    "artifact_type": {
                        "type": "string",
                        "description": "Type of artifact (e.g., config, script, plan)"
                    }
                },
                "required": ["artifact", "artifact_type"]
            }
        ),
        Tool(
            name="troubleshoot",
            description="Have the expert diagnose and suggest fixes for an error",
            inputSchema={
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "The error message or description"
                    },
                    "context": {
                        "type": "string",
                        "description": "Context about what was being attempted"
                    }
                },
                "required": ["error"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if name == "consult":
        return await handle_consult(arguments)
    elif name == "execute":
        return await handle_execute(arguments)
    elif name == "review":
        return await handle_review(arguments)
    elif name == "troubleshoot":
        return await handle_troubleshoot(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def handle_consult(arguments: dict) -> list[TextContent]:
    """Handle consult tool calls."""
    query = arguments["query"]
    context = arguments.get("context", "")

    prompt = f"Question: {query}"
    if context:
        prompt += f"\n\nContext: {context}"

    response_format = """{
    "answer": "string",
    "confidence": "high|medium|low",
    "references": ["list of knowledge sources used"],
    "follow_up_questions": ["clarifying questions if needed"],
    "outside_domain": false
}"""

    try:
        result = expert_llm.query(prompt, response_format)
        response = json.loads(result)
        log_decision(query, response, config)
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    except Exception as e:
        logger.error(f"Consult error: {e}")
        return [TextContent(type="text", text=json.dumps({
            "answer": f"Error processing query: {str(e)}",
            "confidence": "low",
            "references": [],
            "follow_up_questions": [],
            "outside_domain": False
        }))]


async def handle_execute(arguments: dict) -> list[TextContent]:
    """Handle execute tool calls."""
    action = arguments["action"]
    parameters = arguments.get("parameters", {})

    prompt = f"Execute action: {action}\nParameters: {json.dumps(parameters, indent=2)}"

    response_format = """{
    "status": "success|failed|needs_confirmation",
    "result": "output or generated content",
    "error": "error message if failed",
    "next_steps": ["recommended follow-up actions"]
}"""

    try:
        result = expert_llm.query(prompt, response_format)
        response = json.loads(result)
        log_decision(f"Execute: {action}", response, config)
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    except Exception as e:
        logger.error(f"Execute error: {e}")
        return [TextContent(type="text", text=json.dumps({
            "status": "failed",
            "result": None,
            "error": str(e),
            "next_steps": ["Review error and retry"]
        }))]


async def handle_review(arguments: dict) -> list[TextContent]:
    """Handle review tool calls."""
    artifact = arguments["artifact"]
    artifact_type = arguments["artifact_type"]

    prompt = f"Review the following {artifact_type}:\n\n```\n{artifact}\n```"

    response_format = """{
    "assessment": "approved|concerns|rejected",
    "issues": [
        {
            "severity": "error|warning|info",
            "description": "issue description",
            "location": "where in the artifact",
            "suggestion": "how to fix"
        }
    ],
    "suggestions": ["general improvement suggestions"]
}"""

    try:
        result = expert_llm.query(prompt, response_format)
        response = json.loads(result)
        log_decision(f"Review: {artifact_type}", response, config)
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    except Exception as e:
        logger.error(f"Review error: {e}")
        return [TextContent(type="text", text=json.dumps({
            "assessment": "concerns",
            "issues": [{"severity": "error", "description": str(e)}],
            "suggestions": ["Unable to complete review due to error"]
        }))]


async def handle_troubleshoot(arguments: dict) -> list[TextContent]:
    """Handle troubleshoot tool calls."""
    error = arguments["error"]
    context = arguments.get("context", "")

    prompt = f"Troubleshoot this error:\n\nError: {error}"
    if context:
        prompt += f"\n\nContext: {context}"

    response_format = """{
    "diagnosis": "what the error means",
    "root_cause": "underlying cause if known",
    "suggested_fixes": [
        {
            "description": "fix description",
            "steps": ["step 1", "step 2"],
            "confidence": "high|medium|low"
        }
    ],
    "confidence": "high|medium|low"
}"""

    try:
        result = expert_llm.query(prompt, response_format)
        response = json.loads(result)
        log_decision(f"Troubleshoot: {error[:100]}", response, config)
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    except Exception as e:
        logger.error(f"Troubleshoot error: {e}")
        return [TextContent(type="text", text=json.dumps({
            "diagnosis": f"Error during troubleshooting: {str(e)}",
            "root_cause": None,
            "suggested_fixes": [],
            "confidence": "low"
        }))]


async def main():
    """Run the MCP server."""
    logger.info(f"Starting {config['expert']['name']} expert server on port {config['server']['port']}")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
