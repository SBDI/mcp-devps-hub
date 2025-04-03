import base64
import json
import pdb
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import SamplingMessage, CreateMessageRequestParams, CreateMessageResponse
from mcp.server.fastmcp.prompts.base import AssistantMessage, Message, UserMessage
from pydantic import Field

from .clients import Clients, create_api_clients  # Corrected import path
from .clients.groq_client import GroqClient
from .config import settings
from .utilities.logging import get_logger  # Use local logger setup
from .utilities import MIN_COMMENT_RATIO, MAX_COMPLEXITY, SPRINT_DAYS

logger = get_logger(__name__)
logger.setLevel("DEBUG")  # Set logging level to DEBUG

# --- Sampling Callback ---
async def handle_sampling_message(
    ctx: Any,
    params: CreateMessageRequestParams,
) -> CreateMessageResponse:
    """Handle sampling requests from the MCP server.

    This allows the server to request LLM completions through the client,
    enabling more sophisticated AI-powered features.
    """
    logger.info(f"Sampling request received with {len(params.messages)} messages")

    try:
        # Use our Groq client to generate the completion
        groq_client = GroqClient()

        # Convert MCP messages to Groq format
        groq_messages = []
        for msg in params.messages:
            if isinstance(msg, SamplingMessage):
                groq_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })

        # Generate completion with Groq
        completion = await groq_client.generate_completion(
            messages=groq_messages,
            temperature=params.temperature or 0.7,
            max_tokens=params.max_tokens or 1000
        )

        # Return the response
        return CreateMessageResponse(content=completion)

    except Exception as e:
        logger.error(f"Error in sampling callback: {e}")
        return CreateMessageResponse(
            content=f"Error generating response: {e}",
            finish_reason="error"
        )

# --- Lifespan Manager ---
@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[Clients]:
    async with create_api_clients() as clients:
        yield clients

# --- Server Definition ---
required_deps = [
    "httpx",
    "pydantic-settings",
    "jira",
    "PyGithub",
    "slack_sdk",
    "pymsteams",
    # Add others
]

mcp = FastMCP(
    "DevOps Visibility Hub",
    instructions="Provides tools, resources, and prompts for development lifecycle visibility.",
    dependencies=required_deps,
    lifespan=app_lifespan,
    sampling_callback=handle_sampling_message
)

# --- Resources ---
@mcp.resource("jira://project/{project_key}/sprint/{sprint_id}/tasks")
async def get_sprint_tasks(project_key: str, sprint_id: str) -> str:
    """Gets tasks for a Jira sprint."""
    logger.info(f"Resource: Getting tasks for sprint {sprint_id} in {project_key}")
    try:
        # Access clients directly from the global mcp instance
        jira_client = mcp.lifespan_context.jira
        tasks = await jira_client.get_sprint_tasks(project_key, sprint_id)
        return json.dumps({
            "total": len(tasks),
            "tasks": [
                {
                    "key": task.key,
                    "summary": task.fields.summary,
                    "status": task.fields.status.name,
                    "assignee": task.fields.assignee.displayName if task.fields.assignee else None,
                    "story_points": task.fields.customfield_10026,  # Adjust field ID as needed
                } for task in tasks
            ]
        })
    except Exception as e:
        logger.error(f"Error fetching sprint tasks: {e}")
        return json.dumps({"error": str(e)})

@mcp.resource("github://{owner}/{repo}/content")
async def get_github_content(owner: str, repo: str) -> str:
    """Gets content of the root directory in a GitHub repo."""
    return await _get_github_path_content(owner, repo, "")

async def _get_github_path_content(owner: str, repo: str, path: str) -> str:
    """Gets content of a file or lists a directory in a GitHub repo."""
    logger.info(f"Resource: Getting content for {owner}/{repo}/{path}")
    try:
        # Access clients directly from the global mcp instance
        github_client = mcp.lifespan_context.github
        content = await github_client.get_content(owner, repo, path)
        return json.dumps({
            "type": content.type,
            "path": content.path,
            "content": base64.b64decode(content.content).decode() if content.type == "file" else None,
            "entries": [{"name": item.name, "type": item.type} for item in content] if content.type == "dir" else None
        })
    except AttributeError as e:
        logger.error(f"Invalid response format from GitHub API: {e}")
        return json.dumps({"error": "Invalid response format from GitHub API", "details": str(e)})
    except ValueError as e:
        logger.error(f"Invalid content encoding: {e}")
        return json.dumps({"error": "Invalid content encoding", "details": str(e)})
    except Exception as e:
        error_type = e.__class__.__name__
        logger.error(f"{error_type} while fetching GitHub content: {e}")
        return json.dumps({"error": f"GitHub API error: {error_type}", "details": str(e)})

@mcp.resource("cicd://{pipeline_name}/build/{build_number}/status")
async def get_build_status(pipeline_name: str, build_number: str) -> str:
    """Gets the status of a specific CI/CD build."""
    logger.info(f"Resource: Getting status for {pipeline_name} build {build_number}")
    try:
        jenkins_client = mcp.lifespan_context.jenkins
        build_info = await jenkins_client.get_build_info(pipeline_name, build_number)
        return json.dumps({
            "pipeline": pipeline_name,
            "build": build_number,
            "status": build_info["result"],
            "timestamp": build_info["timestamp"],
            "duration": build_info["duration"],
            "url": build_info["url"]
        })
    except Exception as e:
        logger.error(f"Error fetching build status: {e}")
        return json.dumps({"error": str(e)})

# Add more resources for test results, capacity metrics etc.

# --- Tools ---
@mcp.tool()
async def generate_sprint_report(
    project_key: Annotated[str, Field(description="Jira project key (e.g., 'PROJ')")],
    sprint_id: Annotated[int, Field(description="Numeric ID of the Jira sprint")]
) -> str:
    """Generates a report summarizing completed/remaining tasks for a sprint."""
    logger.info(f"Tool: Generating sprint report for {project_key} sprint {sprint_id}")
    try:
        # Fetch sprint tasks
        tasks_json = await get_sprint_tasks(project_key, str(sprint_id))
        tasks_data = json.loads(tasks_json)

        if "error" in tasks_data:
            return f"Error generating report: {tasks_data['error']}"

        # Analyze tasks
        total_tasks = len(tasks_data["tasks"])
        completed_tasks = sum(1 for task in tasks_data["tasks"] if task["status"] == "Done")
        total_points = sum(task["story_points"] or 0 for task in tasks_data["tasks"])
        completed_points = sum(
            task["story_points"] or 0
            for task in tasks_data["tasks"]
            if task["status"] == "Done"
        )

        # Generate report
        report = [
            f"Sprint Report for {project_key} Sprint {sprint_id}",
            "=" * 50,
            f"Total Tasks: {total_tasks}",
            f"Completed Tasks: {completed_tasks} ({(completed_tasks/total_tasks*100):.1f if total_tasks > 0 else 0}%)",
            f"Total Story Points: {total_points}",
            f"Completed Points: {completed_points} ({(completed_points/total_points*100):.1f if total_points > 0 else 0}%)",
            "\nTask Breakdown by Status:",
        ]

        status_counts: dict[str, int] = {}
        for task in tasks_data["tasks"]:
            status_counts[task["status"]] = status_counts.get(task["status"], 0) + 1

        for status, count in status_counts.items():
            report.append(f"- {status}: {count}")

        return "\n".join(report)
    except Exception as e:
        logger.error(f"Error generating sprint report: {e}")
        return f"Error generating report: {e!s}"

@mcp.tool()
async def predict_burndown(
    project_key: Annotated[str, Field(description="Jira project key")],
    sprint_id: Annotated[int, Field(description="Jira sprint ID")]
) -> str:
    """Analyzes sprint progress and historical data to predict burndown."""
    logger.info(f"Tool: Predicting burndown for {project_key} sprint {sprint_id}")
    try:
        jira_client = mcp.lifespan_context.jira

        # Get current sprint data
        current_sprint = await jira_client.get_sprint(sprint_id)
        tasks_json = await get_sprint_tasks(project_key, str(sprint_id))
        tasks_data = json.loads(tasks_json)

        # Calculate current metrics
        total_points = sum(task["story_points"] or 0 for task in tasks_data["tasks"])
        remaining_points = sum(
            task["story_points"] or 0
            for task in tasks_data["tasks"]
            if task["status"] != "Done"
        )

        # Calculate velocity from previous sprints
        past_sprints = await jira_client.get_completed_sprints(project_key, limit=3)
        velocities = []
        for sprint in past_sprints:
            sprint_tasks = await jira_client.get_sprint_tasks(project_key, sprint.id)
            completed_points = sum(
                task.fields.customfield_10026 or 0
                for task in sprint_tasks
                if task.fields.status.name == "Done"
            )
            velocities.append(completed_points)

        avg_velocity = sum(velocities) / len(velocities) if velocities else 0

        # Calculate prediction
        days_remaining = (current_sprint.endDate - datetime.now()).days
        predicted_completion = remaining_points - (avg_velocity * days_remaining / SPRINT_DAYS)

        return (
            f"Burndown Prediction for {project_key} Sprint {sprint_id}\n"
            f"Total Points: {total_points}\n"
            f"Remaining Points: {remaining_points}\n"
            f"Average Team Velocity: {avg_velocity:.1f} points/sprint\n"
            f"Days Remaining: {days_remaining}\n"
            f"Predicted Points at Sprint End: {max(0, predicted_completion):.1f}\n"
            f"Status: {'ON TRACK' if predicted_completion <= 0 else 'AT RISK'}"
        )
    except Exception as e:
        logger.error(f"Error predicting burndown: {e}")
        return f"Error predicting burndown: {e!s}"

@mcp.tool()
async def assess_code_quality(
    owner: Annotated[str, Field(description="GitHub repository owner")],
    repo: Annotated[str, Field(description="GitHub repository name")],
    path: Annotated[str, Field(description="Path to file or directory", default="")]
) -> str:
    """Assesses code quality for a given file or directory."""
    logger.info(f"Tool: Assessing code quality for {owner}/{repo}/{path}")
    try:
        # Get content
        content_json = await _get_github_path_content(owner, repo, path)
        content_data = json.loads(content_json)

        if "error" in content_data:
            return f"Error assessing code quality: {content_data['error']}"

        if content_data["type"] == "file":
            # Analyze single file
            code = content_data["content"]

            # Basic metrics
            lines = code.split("\n")
            total_lines = len(lines)
            code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))
            comment_lines = sum(1 for line in lines if line.strip().startswith("#"))

            # Complexity metrics (simple version)
            complexity = 0
            for line in lines:
                if any(kw in line for kw in ["if", "for", "while", "except", "def", "class"]):
                    complexity += 1

            return (
                f"Code Quality Assessment for {path}\n"
                f"================================\n"
                f"Total Lines: {total_lines}\n"
                f"Lines of Code: {code_lines}\n"
                f"Comment Lines: {comment_lines}\n"
                f"Comment Ratio: {(comment_lines/total_lines*100):.1f}%\n"
                f"Cyclomatic Complexity: {complexity}\n"
                f"\nRecommendations:\n"
                f"- {'Add more comments' if comment_lines/total_lines < MIN_COMMENT_RATIO else 'Comment ratio is good'}\n"
                f"- {'Consider breaking down complex logic' if complexity > MAX_COMPLEXITY else 'Complexity is acceptable'}"
            )
        else:
            # Directory summary
            return (
                f"Directory Summary for {path}\n"
                f"Total files: {len(content_data['entries'])}\n"
                "Use specific file paths for detailed analysis"
            )
    except Exception as e:
        logger.error(f"Error assessing code quality: {e}")
        return f"Error assessing code quality: {e!s}"

@mcp.tool()
async def analyze_code_with_groq(
    owner: Annotated[str, Field(description="GitHub repository owner")],
    repo: Annotated[str, Field(description="GitHub repository name")],
    path: Annotated[str, Field(description="Path to file")]
) -> str:
    """Analyzes code using Groq's AI capabilities."""
    logger.info(f"Tool: Analyzing code with Groq for {owner}/{repo}/{path}")
    try:
        # Get content
        content_json = await _get_github_path_content(owner, repo, path)
        content_data = json.loads(content_json)

        if "error" in content_data:
            return f"Error analyzing code: {content_data['error']}"

        if content_data["type"] != "file":
            return "Please provide a path to a specific file"

        # Determine language from file extension
        language = path.split(".")[-1]

        # Get Groq analysis
        groq_client = mcp.lifespan_context.groq
        analysis = await groq_client.analyze_code(
            code=content_data["content"],
            language=language
        )

        return f"Code Analysis for {path}\n{'='*50}\n{analysis}"

    except Exception as e:
        logger.error(f"Error in Groq analysis: {e}")
        return f"Error analyzing code: {e!s}"

# Add tools for notifications, AI estimation, doc generation

@mcp.tool()
async def generate_ai_insights(
    context: Annotated[str, Field(description="Context information for the AI to analyze")],
    question: Annotated[str, Field(description="Specific question or analysis request")],
) -> str:
    """Generate AI-powered insights using sampling.

    This tool uses MCP sampling to generate insights based on the provided context and question.
    The AI model will analyze the context and provide a detailed response to the question.
    """
    logger.info(f"Tool: Generating AI insights for question: {question}")

    try:
        # Create system message
        system_message = SamplingMessage(
            role="system",
            content="You are an AI assistant specialized in software development and DevOps. "
                    "Analyze the provided context and answer the question with detailed insights."
        )

        # Create user message with context and question
        user_message = SamplingMessage(
            role="user",
            content=f"Context:\n{context}\n\nQuestion: {question}"
        )

        # Use MCP sampling to generate insights
        # This will be handled by the sampling_callback we defined
        response = await mcp.sample_from_llm(
            messages=[system_message, user_message],
            temperature=0.3,  # Lower temperature for more focused responses
            max_tokens=1500   # Allow for detailed responses
        )

        return response.content

    except Exception as e:
        logger.error(f"Error generating AI insights: {e}")
        return f"Error generating insights: {e}"

# --- Prompts ---
@mcp.prompt()
async def sprint_retrospective_guidance(
    project_key: Annotated[str, Field(description="Jira project key")],
    sprint_id: Annotated[int, Field(description="Jira sprint ID")]
) -> list[Message]:
    """Guides a structured sprint retrospective discussion."""
    logger.info(f"Prompt: Generating retrospective guidance for {project_key} sprint {sprint_id}")

    try:
        # Fetch sprint data
        sprint_report = await generate_sprint_report(project_key, sprint_id)
        burndown_prediction = await predict_burndown(project_key, sprint_id)

        messages = [
            UserMessage(
                f"Let's start the retrospective for sprint {sprint_id} in project {project_key}.\n\n"
                f"Sprint Summary:\n{sprint_report}\n\nBurndown Analysis:\n{burndown_prediction}"
            ),
            AssistantMessage(
                "Based on the sprint data, let's structure our retrospective discussion:\n\n"
                "1. Successes 🌟\n"
                "   - What went particularly well this sprint?\n"
                "   - Which tasks were completed ahead of schedule?\n"
                "   - What positive team dynamics did you observe?\n\n"
                "2. Challenges 🤔\n"
                "   - What obstacles did we encounter?\n"
                "   - Were there any unexpected delays?\n"
                "   - Did we have all the resources needed?\n\n"
                "3. Learning Opportunities 📚\n"
                "   - What could we have done differently?\n"
                "   - What processes need improvement?\n"
                "   - What skills or knowledge gaps did we identify?\n\n"
                "4. Action Items 📋\n"
                "   - What specific changes should we implement?\n"
                "   - Who will be responsible for each action item?\n"
                "   - When will we review progress on these items?\n\n"
                "Let's start with successes. What achievements should we celebrate from this sprint?"
            ),
            UserMessage("Please share your thoughts on our successes this sprint."),
        ]

        return messages
    except Exception as e:
        logger.error(f"Error generating retrospective guidance: {e}")
        return [
            UserMessage("An error occurred while preparing the retrospective guidance."),
            AssistantMessage(f"I encountered an error: {e!s}\nLet's proceed with a basic retrospective format instead.")
        ]

# Add prompts for tech debt evaluation, release readiness

# --- Main Execution Function ---
def run_server():
    """Runs the MCP server."""
    logger.debug("Starting run_server()")

    # Check critical configurations
    if not settings.jira_api_token:
        logger.warning("JIRA_API_TOKEN not set")
    if not settings.github_token:
        logger.warning("GITHUB_TOKEN not set")
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY not set")

    print("Starting DevOps Visibility Hub MCP Server...")

    # Add breakpoint before server start
    if "--debug" in sys.argv:
        pdb.set_trace()

    try:
        mcp.run()  # Defaults to stdio
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        raise

if __name__ == "__main__":
    run_server()
