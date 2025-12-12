"""
Requirements Expert MCP Server

An MCP server that wraps an LLM with domain-specific knowledge
to provide expert guidance for transforming project descriptions
into structured Behavior Contracts.
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
server = Server("requirements-expert")

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


def load_template() -> str:
    """Load the Behavior Contract template."""
    template_path = EXPERT_ROOT / "templates" / "behavior-contract.md"
    if template_path.exists():
        return template_path.read_text()
    return ""


# Response models
@dataclass
class ConsultResponse:
    """Response from consulting the expert."""
    answer: str
    confidence: Literal["high", "medium", "low"]
    clarifying_questions: list[str]
    partial_contract: Optional[str]
    outside_domain: bool = False


@dataclass
class ExecuteResponse:
    """Response from executing an action."""
    status: Literal["success", "failed", "needs_more_info"]
    result: Optional[str] = None
    error: Optional[str] = None
    open_questions: list[str] = None

    def __post_init__(self):
        if self.open_questions is None:
            self.open_questions = []


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
    assessment: Literal["complete", "gaps_found", "insufficient"]
    issues: list[Issue]
    missing_sections: list[str]
    suggestions: list[str]


@dataclass
class TroubleshootResponse:
    """Response from troubleshooting unclear requirements."""
    diagnosis: str
    root_cause: Optional[str]
    recommended_questions: list[str]
    confidence: Literal["high", "medium", "low"]


class ExpertLLM:
    """Wrapper for LLM with expert knowledge context."""

    def __init__(self, config: dict):
        self.config = config
        self.client = Anthropic()
        self.knowledge = load_knowledge(config)
        self.template = load_template()
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the system prompt with knowledge context."""
        return f"""You are the Requirements Expert.
Domain: {self.config['expert']['domain']}

Your role is to transform project descriptions into structured Behavior Contracts.
You surface ambiguities as questions, never invent requirements, and never make implementation decisions.

{self.knowledge}

Behavior Contract Template:
{self.template}

Response Guidelines:
1. Preserve user's language and intent
2. Ask clarifying questions for ambiguities (never assume)
3. Prioritize questions by implementation impact: Blocking > Architectural > Edge Case
4. State confidence level (high/medium/low)
5. If asked about implementation, architecture, or timeline - decline and redirect

Boundaries - Refuse these topics:
{json.dumps(self.config.get('boundaries', {}).get('refuse_patterns', []), indent=2)}

If asked about something outside your domain, respond with outside_domain=true and explain the redirect."""

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
            description="Analyze a project description and generate clarifying questions or partial Behavior Contract",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The project or feature description to analyze"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context (existing system, constraints, etc.)"
                    },
                    "answers": {
                        "type": "object",
                        "description": "Answers to previously asked clarifying questions"
                    }
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="execute",
            description="Generate a complete Behavior Contract from gathered information",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The project or feature description"
                    },
                    "answers": {
                        "type": "object",
                        "description": "All gathered answers to clarifying questions"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Generate even if information is incomplete (will document gaps)"
                    }
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="review",
            description="Review an existing requirements document for completeness",
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact": {
                        "type": "string",
                        "description": "The requirements document content to review"
                    },
                    "artifact_type": {
                        "type": "string",
                        "description": "Type of document (behavior_contract, prd, user_story, etc.)"
                    }
                },
                "required": ["artifact", "artifact_type"]
            }
        ),
        Tool(
            name="troubleshoot",
            description="Diagnose why requirements are unclear or blocking implementation",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem": {
                        "type": "string",
                        "description": "Description of the requirements problem"
                    },
                    "context": {
                        "type": "string",
                        "description": "Context about what's unclear or blocked"
                    }
                },
                "required": ["problem"]
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
    description = arguments["description"]
    context = arguments.get("context", "")
    answers = arguments.get("answers", {})

    prompt = f"Analyze this project description and determine what clarifying questions are needed.\n\nDescription: {description}"
    if context:
        prompt += f"\n\nContext: {context}"
    if answers:
        prompt += f"\n\nPreviously answered questions: {json.dumps(answers, indent=2)}"

    prompt += """

Assess the completeness:
- If complete enough, provide a partial or full Behavior Contract draft
- If gaps exist, provide prioritized clarifying questions (Blocking > Architectural > Edge Case)
- Preserve the user's original language where meaningful"""

    response_format = """{
    "answer": "Assessment of the description's completeness",
    "confidence": "high|medium|low",
    "clarifying_questions": ["prioritized list of questions needed"],
    "partial_contract": "Behavior Contract draft if enough info exists, null otherwise",
    "outside_domain": false
}"""

    try:
        result = expert_llm.query(prompt, response_format)
        response = json.loads(result)
        log_decision(description[:100], response, config)
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    except Exception as e:
        logger.error(f"Consult error: {e}")
        return [TextContent(type="text", text=json.dumps({
            "answer": f"Error processing description: {str(e)}",
            "confidence": "low",
            "clarifying_questions": [],
            "partial_contract": None,
            "outside_domain": False
        }))]


async def handle_execute(arguments: dict) -> list[TextContent]:
    """Handle execute tool calls."""
    description = arguments["description"]
    answers = arguments.get("answers", {})
    force = arguments.get("force", False)

    prompt = f"Generate a complete Behavior Contract for this project.\n\nDescription: {description}"
    if answers:
        prompt += f"\n\nGathered information: {json.dumps(answers, indent=2)}"
    if force:
        prompt += "\n\nNote: User wants to proceed even if information is incomplete. Document any gaps in Open Questions."

    prompt += "\n\nGenerate a complete Behavior Contract following the template format."

    response_format = """{
    "status": "success|failed|needs_more_info",
    "result": "The complete Behavior Contract in markdown format",
    "error": "error message if failed",
    "open_questions": ["questions that remain unanswered, if any"]
}"""

    try:
        result = expert_llm.query(prompt, response_format)
        response = json.loads(result)
        log_decision(f"Generate contract: {description[:100]}", response, config)
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    except Exception as e:
        logger.error(f"Execute error: {e}")
        return [TextContent(type="text", text=json.dumps({
            "status": "failed",
            "result": None,
            "error": str(e),
            "open_questions": []
        }))]


async def handle_review(arguments: dict) -> list[TextContent]:
    """Handle review tool calls."""
    artifact = arguments["artifact"]
    artifact_type = arguments["artifact_type"]

    prompt = f"Review this {artifact_type} for completeness as a requirements document.\n\n```\n{artifact}\n```"
    prompt += """

Assess:
1. Does it clearly define the outcome/success criteria?
2. Are behaviors specified with Given/When/Then?
3. Are constraints documented with rationale?
4. Are verification criteria testable?
5. Are open questions documented?"""

    response_format = """{
    "assessment": "complete|gaps_found|insufficient",
    "issues": [
        {
            "severity": "error|warning|info",
            "description": "issue description",
            "location": "section where issue was found",
            "suggestion": "how to address"
        }
    ],
    "missing_sections": ["list of missing required sections"],
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
            "assessment": "gaps_found",
            "issues": [{"severity": "error", "description": str(e)}],
            "missing_sections": [],
            "suggestions": ["Unable to complete review due to error"]
        }))]


async def handle_troubleshoot(arguments: dict) -> list[TextContent]:
    """Handle troubleshoot tool calls."""
    problem = arguments["problem"]
    context = arguments.get("context", "")

    prompt = f"Diagnose why these requirements are unclear or blocking implementation.\n\nProblem: {problem}"
    if context:
        prompt += f"\n\nContext: {context}"

    prompt += """

Identify:
1. What specifically is unclear?
2. What is the root cause (missing info, ambiguity, conflicting requirements)?
3. What questions would resolve this?"""

    response_format = """{
    "diagnosis": "what is unclear and why",
    "root_cause": "underlying cause of the confusion",
    "recommended_questions": ["questions that would resolve the issue"],
    "confidence": "high|medium|low"
}"""

    try:
        result = expert_llm.query(prompt, response_format)
        response = json.loads(result)
        log_decision(f"Troubleshoot: {problem[:100]}", response, config)
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    except Exception as e:
        logger.error(f"Troubleshoot error: {e}")
        return [TextContent(type="text", text=json.dumps({
            "diagnosis": f"Error during troubleshooting: {str(e)}",
            "root_cause": None,
            "recommended_questions": [],
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
