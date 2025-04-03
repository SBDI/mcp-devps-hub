#!/usr/bin/env python
"""
MCP Client Demo - Interacts with the MCP DevOps Hub server in plain text.
This script provides a simple text-based interface to demonstrate the value of the MCP DevOps Hub.
"""

import asyncio
import httpx
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mcp_devops_hub.clients import (
    JiraClient, GitHubClient, GroqClient
)

class MCPClientDemo:
    """A simple text-based client for demonstrating MCP DevOps Hub functionality."""

    def __init__(self):
        """Initialize the demo client."""
        self.jira_client = None
        self.github_client = None
        self.groq_client = None
        self.running = True

        # Default values for demo
        self.default_project = "TEST"
        self.default_sprint = "1"
        self.default_owner = "SBDI"
        self.default_repo = "mcp-devps-hub"

    async def initialize_clients(self):
        """Initialize the API clients."""
        print("Initializing API clients...")

        try:
            self.jira_client = JiraClient()
            print("✅ Jira client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Jira client: {e}")

        try:
            self.github_client = GitHubClient()
            print("✅ GitHub client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize GitHub client: {e}")

        try:
            self.groq_client = GroqClient()
            print("✅ Groq client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Groq client: {e}")

        print("Initialization complete.\n")

    async def close_clients(self):
        """Close all API clients."""
        if self.jira_client:
            await self.jira_client.close()
        if self.github_client:
            await self.github_client.close()
        # Groq client doesn't need explicit closing

    def print_menu(self):
        """Print the main menu."""
        print("\n" + "=" * 50)
        print("MCP DEVOPS HUB DEMO CLIENT")
        print("=" * 50)
        print("1. Sprint Information")
        print("2. GitHub Repository Information")
        print("3. Code Analysis with Groq AI")
        print("4. Generate Sprint Retrospective")
        print("5. Assess Code Quality")
        print("6. Generate AI Insights (MCP Sampling)")
        print("0. Exit")
        print("=" * 50)

    async def handle_sprint_info(self):
        """Handle the sprint information option."""
        print("\n--- Sprint Information ---")

        project = input(f"Enter project key [{self.default_project}]: ") or self.default_project
        sprint_id = input(f"Enter sprint ID [{self.default_sprint}]: ") or self.default_sprint

        print(f"\nFetching sprint tasks for {project}, sprint {sprint_id}...")

        try:
            tasks = await self.jira_client.get_sprint_tasks(project, sprint_id)

            print(f"\nFound {len(tasks)} tasks in the sprint:")
            print("-" * 50)

            # Calculate statistics
            total_points = 0
            completed_points = 0
            status_counts = {}

            for task in tasks:
                # Get story points (if available)
                story_points = getattr(task.fields, 'customfield_10016', None) or 0
                total_points += story_points

                # Count by status
                status = task.fields.status.name
                status_counts[status] = status_counts.get(status, 0) + 1

                # Add to completed points if done
                if status.lower() in ('done', 'closed', 'resolved'):
                    completed_points += story_points

                # Print task details
                assignee = task.fields.assignee.displayName if task.fields.assignee else "Unassigned"
                print(f"{task.key}: {task.fields.summary}")
                print(f"  Status: {status}")
                print(f"  Assignee: {assignee}")
                print(f"  Story Points: {story_points}")
                print()

            # Print summary
            print("-" * 50)
            print(f"Sprint Summary:")
            print(f"Total Tasks: {len(tasks)}")
            print(f"Total Story Points: {total_points}")
            print(f"Completed Points: {completed_points} ({(completed_points/total_points*100):.1f if total_points > 0 else 0}%)")
            print("\nTask Breakdown by Status:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")

        except Exception as e:
            print(f"❌ Error fetching sprint information: {e}")

    async def handle_github_info(self):
        """Handle the GitHub repository information option."""
        print("\n--- GitHub Repository Information ---")

        owner = input(f"Enter repository owner [{self.default_owner}]: ") or self.default_owner
        repo = input(f"Enter repository name [{self.default_repo}]: ") or self.default_repo

        print(f"\nFetching information for {owner}/{repo}...")

        try:
            # Get repository information
            repo_obj = await self.github_client.get_repo(owner, repo)
            if not repo_obj:
                print(f"❌ Repository {owner}/{repo} not found")
                return

            print("\nRepository Information:")
            print("-" * 50)
            print(f"Name: {repo_obj.full_name}")
            print(f"Description: {repo_obj.description}")
            print(f"Default Branch: {repo_obj.default_branch}")
            print(f"Stars: {repo_obj.stargazers_count}")
            print(f"Forks: {repo_obj.forks_count}")
            print(f"Open Issues: {repo_obj.open_issues_count}")
            print(f"Created: {repo_obj.created_at}")
            print(f"Last Updated: {repo_obj.updated_at}")

            # Get content of the root directory
            print("\nRepository Contents:")
            print("-" * 50)

            content = await self.github_client.get_content(owner, repo, "")
            if content:
                for item in content:
                    print(f"{item.type.upper()}: {item.name}")
            else:
                print("No content found in the repository root.")

        except Exception as e:
            print(f"❌ Error fetching GitHub information: {e}")

    async def handle_code_analysis(self):
        """Handle the code analysis option."""
        print("\n--- Code Analysis with Groq AI ---")

        owner = input(f"Enter repository owner [{self.default_owner}]: ") or self.default_owner
        repo = input(f"Enter repository name [{self.default_repo}]: ") or self.default_repo
        path = input("Enter file path to analyze: ")

        if not path:
            print("❌ File path is required")
            return

        print(f"\nFetching and analyzing {path} from {owner}/{repo}...")

        try:
            # Get file content
            content = await self.github_client.get_content(owner, repo, path)
            if not content or not hasattr(content, 'decoded_content'):
                print(f"❌ File {path} not found or is not a file")
                return

            # Get file content as text
            code = content.decoded_content.decode('utf-8')

            # Determine language from file extension
            language = path.split(".")[-1]

            # Analyze code with Groq
            print("\nAnalyzing code with Groq AI...")
            analysis = await self.groq_client.analyze_code(code, language)

            print("\nCode Analysis Results:")
            print("=" * 50)
            print(analysis)
            print("=" * 50)

        except Exception as e:
            print(f"❌ Error analyzing code: {e}")

    async def handle_sprint_retrospective(self):
        """Handle the sprint retrospective option."""
        print("\n--- Generate Sprint Retrospective ---")

        project = input(f"Enter project key [{self.default_project}]: ") or self.default_project
        sprint_id = input(f"Enter sprint ID [{self.default_sprint}]: ") or self.default_sprint

        print(f"\nGenerating retrospective for {project}, sprint {sprint_id}...")

        try:
            # Get sprint tasks
            tasks = await self.jira_client.get_sprint_tasks(project, sprint_id)

            # Calculate statistics
            total_tasks = len(tasks)
            total_points = 0
            completed_points = 0
            status_counts = {}

            for task in tasks:
                # Get story points (if available)
                story_points = getattr(task.fields, 'customfield_10016', None) or 0
                total_points += story_points

                # Count by status
                status = task.fields.status.name
                status_counts[status] = status_counts.get(status, 0) + 1

                # Add to completed points if done
                if status.lower() in ('done', 'closed', 'resolved'):
                    completed_points += story_points

            # Create sprint report
            sprint_report = f"""
Sprint Summary for {project} Sprint {sprint_id}
=================================================
Total Tasks: {total_tasks}
Completed Tasks: {sum(count for status, count in status_counts.items() if status.lower() in ('done', 'closed', 'resolved'))}
Total Story Points: {total_points}
Completed Points: {completed_points} ({(completed_points/total_points*100):.1f if total_points > 0 else 0}%)

Task Breakdown by Status:
{chr(10).join(f'  {status}: {count}' for status, count in status_counts.items())}
"""

            # Generate retrospective with Groq
            messages = [
                {"role": "system", "content": "You are a sprint retrospective facilitator. Generate a structured retrospective based on the sprint data."},
                {"role": "user", "content": f"Let's start the retrospective for sprint {sprint_id} in project {project}.\n\nSprint Summary:\n{sprint_report}"}
            ]

            print("\nGenerating retrospective guidance with Groq AI...")
            retrospective = await self.groq_client.generate_completion(messages)

            print("\nSprint Retrospective:")
            print("=" * 50)
            print(retrospective)
            print("=" * 50)

        except Exception as e:
            print(f"❌ Error generating sprint retrospective: {e}")

    async def handle_code_quality(self):
        """Handle the code quality assessment option."""
        print("\n--- Assess Code Quality ---")

        owner = input(f"Enter repository owner [{self.default_owner}]: ") or self.default_owner
        repo = input(f"Enter repository name [{self.default_repo}]: ") or self.default_repo
        path = input("Enter file path to assess: ")

        if not path:
            print("❌ File path is required")
            return

        print(f"\nAssessing code quality for {path} in {owner}/{repo}...")

        try:
            # Get file content
            content = await self.github_client.get_content(owner, repo, path)
            if not content or not hasattr(content, 'decoded_content'):
                print(f"❌ File {path} not found or is not a file")
                return

            # Get file content as text
            code = content.decoded_content.decode('utf-8')

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

            print("\nCode Quality Assessment:")
            print("=" * 50)
            print(f"Total Lines: {total_lines}")
            print(f"Lines of Code: {code_lines}")
            print(f"Comment Lines: {comment_lines}")
            print(f"Comment Ratio: {(comment_lines/total_lines*100):.1f}%")
            print(f"Cyclomatic Complexity: {complexity}")

            print("\nRecommendations:")
            print(f"- {'Add more comments' if comment_lines/total_lines < 0.1 else 'Comment ratio is good'}")
            print(f"- {'Consider breaking down complex logic' if complexity > 10 else 'Complexity is acceptable'}")
            print("=" * 50)

        except Exception as e:
            print(f"❌ Error assessing code quality: {e}")

    async def handle_ai_insights(self):
        """Handle the AI insights option using MCP sampling."""
        print("\n--- Generate AI Insights (MCP Sampling) ---")

        # Get context information
        context_type = input("Select context type (1=Code, 2=Sprint Data, 3=Custom): ")

        context = ""
        if context_type == "1":
            # Code context
            owner = input(f"Enter repository owner [{self.default_owner}]: ") or self.default_owner
            repo = input(f"Enter repository name [{self.default_repo}]: ") or self.default_repo
            path = input("Enter file path: ")

            if not path:
                print("❌ File path is required")
                return

            try:
                content = await self.github_client.get_content(owner, repo, path)
                if not content or not hasattr(content, 'decoded_content'):
                    print(f"❌ File {path} not found or is not a file")
                    return

                context = f"Code from {owner}/{repo}/{path}:\n\n{content.decoded_content.decode('utf-8')}"
            except Exception as e:
                print(f"❌ Error fetching code: {e}")
                return

        elif context_type == "2":
            # Sprint data context
            project = input(f"Enter project key [{self.default_project}]: ") or self.default_project
            sprint_id = input(f"Enter sprint ID [{self.default_sprint}]: ") or self.default_sprint

            try:
                tasks = await self.jira_client.get_sprint_tasks(project, sprint_id)

                # Format sprint data
                sprint_data = f"Sprint {sprint_id} in project {project}:\n"
                sprint_data += f"Total Tasks: {len(tasks)}\n\n"

                for task in tasks:
                    status = task.fields.status.name
                    assignee = task.fields.assignee.displayName if task.fields.assignee else "Unassigned"
                    sprint_data += f"{task.key}: {task.fields.summary}\n"
                    sprint_data += f"  Status: {status}\n"
                    sprint_data += f"  Assignee: {assignee}\n\n"

                context = sprint_data
            except Exception as e:
                print(f"❌ Error fetching sprint data: {e}")
                return
        else:
            # Custom context
            print("Enter custom context (end with a line containing only 'END'):\n")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                lines.append(line)
            context = "\n".join(lines)

        # Get the question/request
        question = input("\nEnter your question or analysis request: ")
        if not question:
            print("❌ Question is required")
            return

        print("\nGenerating AI insights...")

        try:
            # Call the MCP server's generate_ai_insights tool
            # This will use sampling through our callback
            url = "http://localhost:8000/api/tools/generate_ai_insights"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={
                        "context": context,
                        "question": question
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    insights = result.get("result", "No insights generated")

                    print("\nAI Insights:")
                    print("=" * 50)
                    print(insights)
                    print("=" * 50)
                else:
                    print(f"❌ Error from server: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error generating AI insights: {e}")

    async def run(self):
        """Run the demo client."""
        await self.initialize_clients()

        while self.running:
            self.print_menu()
            choice = input("Enter your choice: ")

            if choice == "1":
                await self.handle_sprint_info()
            elif choice == "2":
                await self.handle_github_info()
            elif choice == "3":
                await self.handle_code_analysis()
            elif choice == "4":
                await self.handle_sprint_retrospective()
            elif choice == "5":
                await self.handle_code_quality()
            elif choice == "6":
                await self.handle_ai_insights()
            elif choice == "0":
                self.running = False
                print("\nExiting demo client...")
            else:
                print("\n❌ Invalid choice. Please try again.")

            if self.running:
                input("\nPress Enter to continue...")

        await self.close_clients()

async def main():
    """Run the MCP client demo."""
    client = MCPClientDemo()
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
