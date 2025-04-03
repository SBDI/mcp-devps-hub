#!/usr/bin/env python
"""
Demo script to test MCP DevOps Hub clients.
This script initializes each client and performs basic operations to verify functionality.
"""

import asyncio
import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mcp_devops_hub.clients import (
    JiraClient, GitHubClient, JenkinsClient, GroqClient
)

async def test_jira_client():
    """Test the Jira client functionality."""
    print("\n=== Testing Jira Client ===")
    try:
        client = JiraClient()
        
        # Test getting sprint information
        sprint_id = 1  # Replace with a valid sprint ID
        project_key = "TEST"  # Replace with a valid project key
        
        print(f"Fetching sprint {sprint_id} information...")
        sprint = await client._run_sync(client._client.sprint, sprint_id)
        if sprint:
            print(f"✅ Successfully fetched sprint: {sprint.name}")
        else:
            print("❌ Failed to fetch sprint")
        
        print(f"Fetching tasks for project {project_key}, sprint {sprint_id}...")
        tasks = await client.get_sprint_tasks(project_key, sprint_id)
        print(f"✅ Found {len(tasks)} tasks in the sprint")
        
        # Display a sample task if available
        if tasks:
            sample_task = tasks[0]
            print(f"Sample task: {sample_task.key} - {sample_task.fields.summary}")
            print(f"Status: {sample_task.fields.status.name}")
            print(f"Assignee: {sample_task.fields.assignee.displayName if sample_task.fields.assignee else 'Unassigned'}")
    
    except Exception as e:
        print(f"❌ Error testing Jira client: {e}")
    finally:
        if 'client' in locals():
            await client.close()

async def test_github_client():
    """Test the GitHub client functionality."""
    print("\n=== Testing GitHub Client ===")
    try:
        client = GitHubClient()
        
        # Test repository access
        owner = "SBDI"  # Replace with a valid GitHub username or organization
        repo_name = "mcp-devps-hub"  # Replace with a valid repository name
        
        print(f"Fetching repository {owner}/{repo_name}...")
        repo = await client.get_repo(owner, repo_name)
        if repo:
            print(f"✅ Successfully connected to repository: {repo.full_name}")
            print(f"Description: {repo.description}")
            print(f"Stars: {repo.stargazers_count}")
            print(f"Forks: {repo.forks_count}")
        else:
            print(f"❌ Repository {owner}/{repo_name} not found")
        
        # Test content retrieval
        path = "README.md"  # Replace with a valid file path
        print(f"Fetching content of {path}...")
        content = await client.get_content(owner, repo_name, path)
        if content:
            if hasattr(content, 'decoded_content'):
                # Single file
                print(f"✅ Successfully fetched file content ({len(content.decoded_content.decode())} bytes)")
                print("First few lines:")
                print("\n".join(content.decoded_content.decode().split("\n")[:5]))
            else:
                # Directory listing
                print(f"✅ Successfully fetched directory listing ({len(content)} items)")
                for item in list(content)[:5]:  # Show first 5 items
                    print(f"- {item.name} ({item.type})")
        else:
            print(f"❌ Content at path '{path}' not found")
    
    except Exception as e:
        print(f"❌ Error testing GitHub client: {e}")
    finally:
        if 'client' in locals():
            await client.close()

async def test_jenkins_client():
    """Test the Jenkins client functionality."""
    print("\n=== Testing Jenkins Client ===")
    try:
        client = JenkinsClient()
        
        if not client._client:
            print("⚠️ Jenkins client not configured. Skipping tests.")
            return
        
        # Test job information retrieval
        job_name = "main-pipeline"  # Replace with a valid job name
        
        print(f"Fetching job information for {job_name}...")
        job_info = await client.get_job_info(job_name)
        if job_info:
            print(f"✅ Successfully fetched job information")
            print(f"Job name: {job_info.get('name', 'N/A')}")
            print(f"URL: {job_info.get('url', 'N/A')}")
            print(f"Buildable: {job_info.get('buildable', False)}")
        else:
            print(f"❌ Job '{job_name}' not found")
        
        # Test build information retrieval
        build_number = "1"  # Replace with a valid build number
        print(f"Fetching build information for {job_name} #{build_number}...")
        build_info = await client.get_build_info(job_name, build_number)
        if build_info:
            print(f"✅ Successfully fetched build information")
            print(f"Build number: {build_info.get('number', 'N/A')}")
            print(f"Result: {build_info.get('result', 'N/A')}")
            print(f"Duration: {build_info.get('duration', 0) / 1000} seconds")
        else:
            print(f"❌ Build #{build_number} for job '{job_name}' not found")
    
    except Exception as e:
        print(f"❌ Error testing Jenkins client: {e}")
    finally:
        if 'client' in locals():
            await client.close()

async def test_groq_client():
    """Test the Groq client functionality."""
    print("\n=== Testing Groq Client ===")
    try:
        client = GroqClient()
        
        # Test simple completion
        prompt = "What are the key benefits of DevOps practices?"
        print(f"Generating completion for prompt: '{prompt}'")
        
        messages = [
            {"role": "system", "content": "You are a DevOps expert providing concise information."},
            {"role": "user", "content": prompt}
        ]
        
        response = await client.generate_completion(messages, max_tokens=200)
        if response:
            print("✅ Successfully generated completion")
            print("\nGroq Response:")
            print("-" * 50)
            print(response)
            print("-" * 50)
        else:
            print("❌ Failed to generate completion")
        
        # Test code analysis
        code_sample = """
def calculate_fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
        
# Calculate the 10th Fibonacci number
result = calculate_fibonacci(10)
print(f"The 10th Fibonacci number is {result}")
"""
        print("\nAnalyzing code sample...")
        analysis = await client.analyze_code(code_sample, "python")
        if analysis:
            print("✅ Successfully analyzed code")
            print("\nCode Analysis:")
            print("-" * 50)
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
            print("-" * 50)
        else:
            print("❌ Failed to analyze code")
    
    except Exception as e:
        print(f"❌ Error testing Groq client: {e}")

async def main():
    """Run all client tests."""
    print("=== MCP DevOps Hub Client Demo ===")
    print("Testing each client to verify functionality...")
    
    # Test each client
    await test_jira_client()
    await test_github_client()
    await test_jenkins_client()
    await test_groq_client()
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
