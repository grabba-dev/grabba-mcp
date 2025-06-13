# Grabba MCP Server

This repository contains the Grabba Microservice Connector Protocol (MCP) server, designed to expose Grabba API functionalities as a set of callable tools. Built on `FastMCP`, this server allows AI agents, orchestrators (like LangChain), and other applications to seamlessly interact with the Grabba data extraction and management services.

## Table of Contents

1.  [Features](#features)
2.  [Getting Started](#getting-started)
      * [Prerequisites](#prerequisites)
      * [Installation](#installation)
          * [Via PyPI (Recommended)](#via-pypi-recommended)
          * [From Source (Development)](#from-source-development)
      * [Running the Server](#running-the-server)
          * [Locally](#locally)
          * [Docker Container](#docker-container)
          * [Public Instance](#public-instance)
3.  [Configuration](#configuration)
      * [Environment Variables](#environment-variables)
      * [Command-Line Arguments](#command-line-arguments)
4.  [Available Tools](#available-tools)
      * [Authentication](#authentication)
      * [Tool Details](#tool-details)
5.  [Connecting to the MCP Server](#connecting-to-the-mcp-server)
      * [Python Client (LangChain Example)](#python-client-langchain-example)
          * [Streamable HTTP Transport](#streamable-http-transport)
          * [Stdio Transport (for Docker-in-Docker or specific use cases)](#stdio-transport-for-docker-in-docker-or-specific-use-cases)
6.  [Development Notes](#development-notes)
      * [Project Structure](#project-structure)
      * [Running Tests](#running-tests)
7.  [Links & Resources](#links--resources)
8.  [License](#license)

-----

## Features

  * **Grabba API Exposure:** Exposes key Grabba API functionalities (data extraction, job management, statistics) as accessible tools.
  * **Multiple Transports:** Supports `stdio`, `streamable-http`, and `sse` transports, offering flexibility for different deployment and client scenarios.
  * **Dependency Injection:** Leverages FastAPI's robust dependency injection for secure and efficient `GrabbaService` initialization (e.g., handling API keys).
  * **Containerized Deployment:** Optimized for Docker for easy packaging and deployment.
  * **Configurable:** Allows configuration via environment variables and command-line arguments.

-----

## Getting Started

### Prerequisites

  * Python 3.10+
  * Docker (for containerized deployment)
  * A Grabba API Key (you can get one from the [Grabba website](https://www.grabba.dev/))

### Installation

#### Via PyPI (Recommended)

The `grabba-mcp` package is available on PyPI. This is the simplest way to get started.

```bash
pip install grabba-mcp
```

#### From Source (Development)

If you plan to contribute or modify the server, you'll want to install from source.

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/grabba-dev/grabba-mcp
    cd grabba-mcp
    ```

2.  **Install Poetry:**
    If you don't have Poetry installed, follow their official guide:

    ```bash
    pip install poetry
    ```

3.  **Install project dependencies:**
    Navigate to the `apps/mcp` directory where `pyproject.toml` resides, then install:

    ```bash
    cd apps/mcp
    poetry install
    ```

### Running the Server

#### Locally

After installation (either via `pip` or from source), you can run the server.

1.  **Create a `.env` file:**
    In the `apps/mcp` directory (if running from source) or the directory from which you'll execute the `grabba-mcp` command, create a `.env` file and add your Grabba API key:

    ```dotenv
    API_KEY="YOUR_API_KEY_HERE"
    # Optional: configure the server port
    PORT=8283
    # Optional: configure the default transport (overridden by CLI)
    MCP_SERVER_TRANSPORT="streamable-http"
    ```

2.  **Execute the server:**

      * **If installed via `pip`:**

        ```bash
        grabba-mcp
        ```

        To specify a transport via command line:

        ```bash
        grabba-mcp streamable-http
        ```

      * **If running from source (using Poetry):**

        ```bash
        cd apps/mcp
        poetry run python src/server.py
        ```

        To specify a transport via command line:

        ```bash
        poetry run python src/server.py stdio
        ```

    You should see output indicating the server is starting and listening on the specified port (e.g., `http://0.0.0.0:8283`) if using HTTP transports. Note that the `stdio` transport will exit after a single request/response cycle, making it unsuitable for persistent services.

#### Docker Container

A pre-built Docker image is available on Docker Hub, making deployment straightforward.

1.  **Pull the image:**

    ```bash
    docker pull itsobaa/grabba-mcp:latest
    ```

2.  **Run the container:**
    For a persistent server, you'll typically use the `streamable-http` transport and map ports.

    ```bash
    docker run -d \
      -p 8283:8283 \
      -e API_KEY="YOUR_API_KEY_HERE" \
      -e MCP_SERVER_TRANSPORT="streamable-http" \
      itsobaa/grabba-mcp:latest
    ```

    You can also use `docker-compose` for more complex setups:

    ```yaml
    # docker-compose.yml
    version: '3.8'
    services:
      grabba-mcp:
        image: itsobaa/grabba-mcp:latest
        container_name: grabba-mcp
        environment:
          API_KEY: ${API_KEY} # Reads from a .env file next to docker-compose.yml
          MCP_SERVER_TRANSPORT: streamable-http
          PORT: 8283
        ports:
          - "8283:8283"
        healthcheck:
          test: ["CMD-SHELL", "curl -f http://localhost:8283/tools/openapi.json || exit 1"]
          interval: 10s
          timeout: 5s
          retries: 5
    ```

    With a `docker-compose.yml` file, create a `.env` file next to it (e.g., `API_KEY="YOUR_API_KEY_HERE"`) and run:

    ```bash
    docker-compose up -d
    ```

#### Public Instance

The Grabba MCP Server is publicly accessible at:

  * **URL:** `https://mcp.grabba.dev/`
  * **Transports:** Supports `sse` and `streamable-http`.
  * **Authentication:** Requires an `API_KEY` header with your Grabba API key.

-----

## Configuration

The server can be configured via environment variables and command-line arguments.

### Environment Variables

  * **`API_KEY`** (Required): Your Grabba API key. This is critical for authenticating with Grabba services.
  * **`PORT`** (Optional, default: `8283`): The port on which the MCP server's HTTP transports (`streamable-http`, `sse`) will listen.
  * **`MCP_SERVER_TRANSPORT`** (Optional, default: `stdio`): The default transport protocol for the MCP server. Can be `stdio`, `streamable-http`, or `sse`.

### Command-Line Arguments

The server also accepts a single positional command-line argument which overrides `MCP_SERVER_TRANSPORT`:

```bash
grabba-mcp [transport_protocol]
# or for source: python src/server.py [transport_protocol]
```

  * `[transport_protocol]`: Can be `stdio`, `streamable-http`, or `sse`.
      * Example: `grabba-mcp streamable-http`

-----

## Available Tools

The Grabba MCP Server exposes a suite of tools that wrap the Grabba Python SDK functionalities.

### Authentication

For `streamable-http` and `sse` transports, authentication is performed by including an **`API_KEY`** HTTP header with your Grabba API Key.
Example: `API_KEY: YOUR_API_KEY_HERE`

For `stdio` transport, the **`API_KEY`** environment variable must be set in the environment where the `grabba-mcp` command is executed, as there are no HTTP headers in this communication mode.

### Tool Details

#### `extract_data`

  * **Description:** Schedules a new data extraction job with Grabba. Suitable for web search tasks.
  * **Input:** `Job` object (Pydantic model) detailing the extraction tasks.
  * **Output:** `tuple[str, Optional[Dict]]` - A message and the `JobResult` as a dictionary.

#### `schedule_existing_job`

  * **Description:** Schedules an existing Grabba job to run immediately.
  * **Input:** `job_id` (string) - The ID of the existing job.
  * **Output:** `tuple[str, Optional[Dict]]` - A message and the `JobResult` as a dictionary.

#### `fetch_all_jobs`

  * **Description:** Fetches all Grabba jobs for the current user.
  * **Input:** None.
  * **Output:** `tuple[str, Optional[List[Job]]]` - A message and a list of `Job` objects.

#### `fetch_specific_job`

  * **Description:** Fetches details of a specific Grabba job by its ID.
  * **Input:** `job_id` (string) - The ID of the job.
  * **Output:** `tuple[str, Optional[Job]]` - A message and the `Job` object.

#### `delete_job`

  * **Description:** Deletes a specific Grabba job.
  * **Input:** `job_id` (string) - The ID of the job to delete.
  * **Output:** `tuple[str, None]` - A success message.

#### `fetch_job_result`

  * **Description:** Fetches results of a completed Grabba job by its result ID.
  * **Input:** `job_result_id` (string) - The ID of the job result.
  * **Output:** `tuple[str, Optional[Dict]]` - A message and the job result data as a dictionary.

#### `delete_job_result`

  * **Description:** Deletes results of a completed Grabba job.
  * **Input:** `job_result_id` (string) - The ID of the job result to delete.
  * **Output:** `tuple[str, None]` - A success message.

#### `fetch_stats_data`

  * **Description:** Fetches usage statistics and current user token balance for Grabba.
  * **Input:** None.
  * **Output:** `tuple[str, Optional[JobStats]]` - A message and the `JobStats` object.

#### `estimate_job_cost`

  * **Description:** Estimates the cost of a Grabba job before creation or scheduling.
  * **Input:** `Job` object (Pydantic model) detailing the extraction tasks.
  * **Output:** `tuple[str, Optional[Dict]]` - A message and the estimated cost details as a dictionary.

#### `create_job`

  * **Description:** Creates a new data extraction job in Grabba without immediately scheduling it for execution.
  * **Input:** `Job` object (Pydantic model) detailing the extraction tasks.
  * **Output:** `tuple[str, Optional[Job]]` - A message and the created `Job` object.

#### `fetch_available_regions`

  * **Description:** Fetches a list of all available puppet (web agent) regions that can be used for scheduling web data extractions.
  * **Input:** None.
  * **Output:** `tuple[str, Optional[List[PuppetRegion]]]` - A message and a list of `PuppetRegion` objects.

-----

## Connecting to the MCP Server

The `MultiServerMCPClient` from `mcp.client` is designed to connect to FastMCP servers.

### Python Client (LangChain Example)

This example assumes you have the `mcp-client` package installed (often as part of a larger LangChain/Agent setup), along with `grabba` and `pydantic`.

```python
import asyncio
import os
from typing import List, Dict, Optional
from langchain_core.tools import BaseTool, Tool
from mcp.models.mcp_server_config import McpServerConfig, McpServer
from mcp.client.transports.streamable_http import StreamableHttpConnection
from mcp.client.transports.stdio import StdioConnection
from mcp.client.multi_server_client import MultiServerMCPClient
from grabba import Job, JobStats, PuppetRegion # Import necessary Grabba Pydantic models
from dotenv import load_dotenv # For loading API key from .env

async def connect_and_use_mcp_tools(mcp_server_configs: List[McpServerConfig], api_key: Optional[str] = None) -> List[Tool]:
    """
    Connects to the MCP server(s), discovers its tools, and wraps them as LangChain Tools.
    Handles API key injection for HTTP connections.
    """
    try:
        mcp_client_config = {}
        for config in mcp_server_configs:
            # Pydantic V2 model validation
            mcp_server_model = McpServer.model_validate(config.mcp_server.model_dump())
            
            connection_headers = {}
            if api_key:
                # Use standard header name for API keys
                connection_headers["API_KEY"] = api_key 

            if mcp_server_model.transport == "streamable_http":
                server_params: StreamableHttpConnection = {
                    "transport": "streamable_http",
                    "url": str(mcp_server_model.url),
                    "env": config.env_variables or {}, # For other env variables, if any
                    "headers": connection_headers # Pass headers for HTTP transports
                }
            elif mcp_server_model.transport == "stdio":
                server_params: StdioConnection = {
                    "transport": "stdio",
                    "command": mcp_server_model.command, 
                    "args": mcp_server_model.args, 
                    "env": config.env_variables # For stdio, env maps to subprocess env vars
                }
            else:
                raise ValueError(f"Unsupported transport: {mcp_server_model.transport}")

            print(f"Client connecting with params: {server_params}")
            mcp_client_config[mcp_server_model.name] = server_params
        
        mcp_client = MultiServerMCPClient(mcp_client_config)
        tools: List[BaseTool] = await mcp_client.get_tools()
        print(f"Successfully loaded {len(tools)} tools.")
        return tools
    except Exception as e:
        print(f"Error connecting to MCP server or loading tools: {e}")
        return []


async def main():
    load_dotenv() # Load API key from a client-side .env file
    API_KEY = os.getenv("API_KEY", "YOUR_API_KEY_HERE_IF_NOT_ENV")

    # --- Configuration for Streamable HTTP Transport (Local or Public Instance) ---
    # For local: url="http://localhost:8283"
    # For public: url="https://mcp.grabba.dev/"
    http_mcp_config = McpServerConfig(
        mcp_server=McpServer(
            name="grabba-agent-http",
            transport="streamable_http",
            url="http://localhost:8283" # Or "https://mcp.grabba.dev/" for public
        )
    )

    print("\n--- Connecting via Streamable HTTP ---")
    http_tools = await connect_and_use_mcp_tools(
        mcp_server_configs=[http_mcp_config],
        api_key=API_KEY
    )

    if http_tools:
        print("\nAvailable HTTP Tools:")
        for tool in http_tools:
            print(f"- {tool.name}: {tool.description.split('.')[0]}.")
        
        # Example: Using the extract_data tool (adjust as per your Job Pydantic model)
        extract_tool = next((t for t in http_tools if t.name == "extract_data"), None)
        if extract_tool:
            print("\n--- Testing extract_data tool via HTTP ---")
            sample_job = Job(
                url="https://example.com/some-page",
                type="markdown", # or "pdf", "html" etc.
                parser="text-content",
                strategy="auto"
                # ... other required fields for Job
            )
            try:
                result_msg, result_data = await extract_tool.ainvoke({"extraction_data": sample_job})
                print(f"Extraction Result (HTTP): {result_msg}")
                if result_data:
                    print(f"Extraction Data (HTTP): {result_data.get('extracted_text', 'No text extracted')[:100]}...") # Print first 100 chars
            except Exception as e:
                print(f"Error calling extract_data via HTTP: {e}")
        else:
            print("extract_data tool not found in HTTP tools.")

        # Example: Using fetch_all_jobs tool
        fetch_jobs_tool = next((t for t in http_tools if t.name == "fetch_all_jobs"), None)
        if fetch_jobs_tool:
            print("\n--- Testing fetch_all_jobs tool via HTTP ---")
            try:
                result_msg, jobs_list = await fetch_jobs_tool.ainvoke({})
                print(f"Fetch Jobs Result (HTTP): {result_msg}")
                if jobs_list:
                    print(f"Fetched {len(jobs_list)} jobs.")
                    for job in jobs_list[:2]: # Print first 2 jobs
                        print(f"  - Job ID: {job.job_id}, URL: {job.url}")
            except Exception as e:
                print(f"Error calling fetch_all_jobs via HTTP: {e}")
        
        # Example: Using fetch_stats_data tool
        fetch_stats_tool = next((t for t in http_tools if t.name == "fetch_stats_data"), None)
        if fetch_stats_tool:
            print("\n--- Testing fetch_stats_data tool via HTTP ---")
            try:
                result_msg, stats_data = await fetch_stats_tool.ainvoke({})
                print(f"Fetch Stats Result (HTTP): {result_msg}")
                if stats_data:
                    print(f"Token Balance (HTTP): {stats_data.token_balance}")
                    print(f"Jobs Run (HTTP): {stats_data.jobs_run_count}")
            except Exception as e:
                print(f"Error calling fetch_stats_data via HTTP: {e}")

    # --- Configuration for Stdio Transport (e.g., to a Docker container running the server) ---
    # This assumes you have the 'itsobaa/grabba-mcp:latest' Docker image available.
    # The client launches a temporary Docker container for each tool call.
    stdio_mcp_config = McpServerConfig(
        mcp_server=McpServer(
            name="grabba-agent-stdio",
            transport="stdio",
            command="docker",
            args=[
                "run",
                "-i",          # Keep STDIN open for interactive communication
                "--rm",        # Remove container after exit
                "itsobaa/grabba-mcp:latest", # The Docker Hub image for Grabba MCP server
                "grabba-mcp", "stdio" # Command to run the server in stdio mode inside container
            ],
            env_variables={"API_KEY": API_KEY} # Pass API key as env var for stdio
        )
    )

    print("\n--- Connecting via Stdio (to Docker container as a subprocess) ---")
    stdio_tools = await connect_and_use_mcp_tools(
        mcp_server_configs=[stdio_mcp_config],
        api_key=API_KEY # Client might still pass for internal consistency, though env_variables is primary for stdio
    )

    if stdio_tools:
        print("\nAvailable Stdio Tools:")
        for tool in stdio_tools:
            print(f"- {tool.name}: {tool.description.split('.')[0]}.")
        
        # Example: Using the fetch_available_regions tool via Stdio
        fetch_regions_tool = next((t for t in stdio_tools if t.name == "fetch_available_regions"), None)
        if fetch_regions_tool:
            print("\n--- Testing fetch_available_regions tool via Stdio ---")
            try:
                result_msg, regions_list = await fetch_regions_tool.ainvoke({})
                print(f"Fetch Regions Result (Stdio): {result_msg}")
                if regions_list:
                    print(f"Fetched {len(regions_list)} regions.")
                    for region in regions_list[:3]: # Print first 3 regions
                        print(f"  - {region.display_name} ({region.code})")
            except Exception as e:
                print(f"Error calling fetch_available_regions via Stdio: {e}")
        else:
            print("fetch_available_regions tool not found in Stdio tools.")

if __name__ == "__main__":
    asyncio.run(main())
```

-----

## Development Notes

### Project Structure

```
your_project_root/
├── src/
│   └── server.py               # Main FastMCP server application
├── .env                        # Environment variables for local development
├── pyproject.toml              # Poetry project configuration
└── poetry.lock                 # Poetry dependency lock file
├── Dockerfile                  # Docker build instructions for the server
├── docker-compose.yml          # Docker Compose configuration for local development/deployment
├── .dockerignore               # Files to ignore during Docker build
├── .env                        # Example .env for docker-compose (for API_KEY)
├── README.md                   # This documentation file
├── pyproject.toml              # Root pyproject.toml (if using monorepo structure)
├── poetry.lock                 # Root poetry.lock (if using monorepo structure)
├── src/                        # Source code (often for the root project if it's a monorepo)
├── tests/                      # Project tests
└── ... (other project files like dist, docs, tox.ini, project.json etc.)
```

### Running Tests

To run tests (as configured by your `pyproject.toml`):

```bash
poetry run pytest
```

-----

## Links & Resources

  * **Grabba Website:** [https://www.grabba.dev/](https://www.grabba.dev/)
  * **Grabba MCP Server Public Instance:** [https://mcp.grabba.dev/](https://mcp.grabba.dev/)
  * **GitHub Repository:** [https://github.com/grabba-dev/grabba-mcp](https://github.com/grabba-dev/grabba-mcp)
  * **Docker Hub Image:** [https://hub.docker.com/r/itsobaa/grabba-mcp](https://www.google.com/search?q=https://hub.docker.com/r/itsobaa/grabba-mcp)
  * **PyPI Package:** [https://pypi.org/project/grabba-mcp/](https://www.google.com/search?q=https://pypi.org/project/grabba-mcp/)

-----

## License

This project is licensed under the Proprietary License. Please see the `LICENSE` file in the repository root for full details.

-----