import sys
import asyncio
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List, Dict
from grabba import (
    Grabba, Job, JobResult, JobStats, GetJobResponse, GetJobsResponse,
    JobExecutionStatus, GetJobResultResponse, JobExecutionResponse,
    JobCreationResponse, JobEstimatedCostResponse, PuppetRegion,
    JobStatsResponse
)


class ServerConfig(BaseSettings):
    PORT: int = Field(8283, description="The PORT the MCP server should run on.")
    API_KEY: str = Field(None, description="The API key for accessing the Grabba python SDK.")
    MCP_SERVER_TRANSPORT: str = Field("stdio", description="The transport protocol for the MCP mcp.")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

class GrabbaService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key cannot be empty.")
        self.grabba = Grabba(api_key)

    async def fetch_stats_data(self) -> tuple[str, Optional[JobStats]]:
        """Fetch usage stats and user token balance"""
        try:
            result: JobStatsResponse = self.grabba.get_stats()
            return result.message, result.job_stats
        except Exception as err:
            return f"Error fetching usage stats: {str(err)}", None

    async def estimate_job_cost(self, extraction_data: Job) -> tuple[str, Optional[List[Job]]]:
        """Get the estimated cost of a job before creating or scheduling it"""
        try:
            result: JobEstimatedCostResponse = self.grabba.estimate_job_cost(job=extraction_data)
            return result.message, result.job_estimated_cost
        except Exception as err:
            return f"Error estimating job cost: {str(err)}", None

    async def extract_data(self, extraction_data: Job) -> tuple[str, Optional[Dict]]:
        """Schedule a new data extraction job. [Web Search Tool - when used with markdown tasks]"""
        try:
            result: JobExecutionResponse = self.grabba.extract(job=extraction_data)
            if result.status == JobExecutionStatus.SUCCESS:
                job_result: JobResult = result.job_result
                return result.message, job_result
            return result.message, result.job_result
        except Exception as err:
            return f"Error scheduling job: {str(err)}", None

    async def create_job(self, extraction_data: Job) -> tuple[str, Optional[Job]]:
        """Create a new data extraction job (Without scheduling it)"""
        try:
            result: JobCreationResponse = self.grabba.create_job(job=extraction_data)
            return result.message, result.job
        except Exception as err:
            return f"Error creating job: {str(err)}", None
        
    async def schedule_job(self, job_id: str) -> tuple[str, Optional[Dict]]:
        """Schedule an existing job to run immediately"""
        try:
            result: JobExecutionResponse = self.grabba.schedule_job(job_id=job_id)
            return result.message, result.job_result
        except Exception as err:
            return f"Error scheduling job: {str(err)}", None

    async def fetch_jobs_data(self) -> tuple[str, Optional[List[Job]]]:
        """Fetch all jobs for the current user"""
        try:
            result: GetJobsResponse = self.grabba.get_jobs()
            return result.message, result.jobs
        except Exception as err:
            return f"Error fetching jobs: {str(err)}", None

    async def fetch_job_data(self, job_id: str) -> tuple[str, Optional[Job]]:
        """Fetch details of a specific job"""
        try:
            result: GetJobResponse = self.grabba.get_job(job_id)
            return result.message, result.job
        except Exception as err:
            return f"Error fetching job: {str(err)}", None

    async def delete_job_data(self, job_id: str) -> tuple[str, None]:
        """Delete a specific job"""
        try:
            self.grabba.delete_job(job_id)
            return f"Successfully deleted job {job_id}", None
        except Exception as err:
            return f"Error deleting job: {str(err)}", None

    async def fetch_job_result_data(self, job_result_id: str) -> tuple[str, Optional[Dict]]:
        """Fetch results of a completed job"""
        try:
            result: GetJobResultResponse = self.grabba.get_job_result(job_result_id)
            return result.message, result.job_result
        except Exception as err:
            return f"Error fetching job results: {str(err)}", None

    async def delete_job_result_data(self, job_result_id: str) -> tuple[str, None]:
        """Delete results of a completed job"""
        try:
            self.grabba.delete_job_result(job_result_id)
            return f"Successfully deleted job result {job_result_id}", None
        except Exception as err:
            return f"Error deleting job results: {str(err)}", None

    async def fetch_available_regions(self) -> tuple[str, Optional[List[Dict[str, PuppetRegion]]]]:
        """Fetch all available puppet (web agent) regions for scheduling web data extractions."""
        try:
            return "Fetched available regions successfully", self.grabba.get_available_regions()
        except Exception as err:
            return f"Error fetching jobs: {str(err)}", None


# Load environment variables from .env file
load_dotenv()

# Instantiate ServerConfig
server_config = ServerConfig()

# === ARGUMENT PARSING LOGIC ===
if len(sys.argv) > 1:
    transport = sys.argv[1]
    # Check if the first argument is a known transport type
    valid_transports = ["stdio", "streamable-http", "sse"]
    if transport in valid_transports:
        server_config.MCP_SERVER_TRANSPORT = transport
        print(f"Overriding transport protocol from command line: {server_config.MCP_SERVER_TRANSPORT}")


# Initialize the MCP server
mcp = FastMCP(name="grabba-agent")

# Helper function to get GrabbaService instance within tool
async def _get_grabba_service_instance() -> GrabbaService:
    """
    Resolves the GrabbaService dependency.
    This is called by each tool to get an authenticated GrabbaService instance.
    """
    headers = get_http_headers()
    # Get API_KEY from headers
    api_key = headers.get("api_key") or server_config.API_KEY 
    if not api_key:
        raise ValueError("API Key is missing. Provide it via API_KEY header or API_KEY env var.")
    return GrabbaService(api_key=api_key)


#############################
#   Tools SPecifications    #
#############################


@mcp.tool(
    name="fetch_stats_data",
    description="Fetches usage statistics and current user token balance for Grabba. Takes no parameters.",
    tags={"billing", "usage"}
)
async def fetch_stats_data_tool() -> tuple[str, Optional[JobStats]]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.fetch_stats_data()


@mcp.tool(
    name="estimate_job_cost",
    description="Estimates the cost of a Grabba job before creation or scheduling. Requires a 'Job' object detailing the extraction tasks.",
    tags={"billing"}
)
async def estimate_job_cost_tool(extraction_data: Job) -> tuple[str, Optional[Dict]]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.estimate_job_cost(extraction_data)


@mcp.tool(
    name="create_job",
    description="Creates a new data extraction job in Grabba without immediately scheduling it for execution. Requires a 'Job' object detailing the extraction tasks.",
    tags={"management"}
)
async def create_job_tool(extraction_data: Job) -> tuple[str, Optional[Job]]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.create_job(extraction_data)


@mcp.tool(
    name="extract_data",
    description="Schedules a new data extraction job with Grabba. Requires a 'Job' object detailing the extraction tasks.",
    tags={"catalog", "search"},
)
async def extract_data_tool(extraction_data: Job) -> tuple[str, Optional[Dict]]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.extract_data(extraction_data)


@mcp.tool(
    name="schedule_existing_job",
    description="Schedules an existing Grabba job to run immediately. Requires the 'job_id' of the existing job."
)
async def schedule_job_tool(job_id: str) -> tuple[str, Optional[Dict]]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.schedule_job(job_id)


@mcp.tool(
    name="fetch_all_jobs",
    description="Fetches all Grabba jobs for the current user. Takes no parameters."
)
async def fetch_jobs_data_tool() -> tuple[str, Optional[List[Job]]]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.fetch_jobs_data()


@mcp.tool(
    name="fetch_specific_job",
    description="Fetches details of a specific Grabba job by its ID. Requires the 'job_id' of the job."
)
async def fetch_job_data_tool(job_id: str) -> tuple[str, Optional[Job]]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.fetch_job_data(job_id)


@mcp.tool(
    name="delete_job",
    description="Deletes a specific Grabba job. Requires the 'job_id' of the job to delete."
)
async def delete_job_data_tool(job_id: str) -> tuple[str, None]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.delete_job_data(job_id)


@mcp.tool(
    name="fetch_job_result",
    description="Fetches results of a completed Grabba job by its result ID. Requires the 'job_result_id' of the result."
)
async def fetch_job_result_data_tool(job_result_id: str) -> tuple[str, Optional[Dict]]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.fetch_job_result_data(job_result_id)


@mcp.tool(
    name="delete_job_result",
    description="Deletes results of a completed Grabba job. Requires the 'job_result_id' of the result to delete."
)
async def delete_job_result_data_tool(job_result_id: str) -> tuple[str, None]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.delete_job_result_data(job_result_id)


@mcp.tool(
    name="fetch_available_regions",
    description="Fetches a list of all available puppet (web agent) regions that can be used for scheduling web data extractions. Takes no parameters.",
    tags={"configuration"}
)
async def fetch_available_regions_tool() -> tuple[str, Optional[List[PuppetRegion]]]:
    grabba_service = await _get_grabba_service_instance()
    return await grabba_service.fetch_available_regions()


def main():
    if server_config.MCP_SERVER_TRANSPORT == "streamable-http":        
        # Start the MCP server using FastMCP's built-in run method
        # This will handle HTTP communication protocol (e.g., streamable-http)
        print("Starting Grabba MCP server (streamable-http transport)...")
        asyncio.run(mcp.run_streamable_http_async(
            host="0.0.0.0", 
            port=server_config.PORT, 
            path="/"
        ))

    elif server_config.MCP_SERVER_TRANSPORT == "sse":
        # Start the MCP server using FastMCP's built-in run method
        # This will handle SSE communication protocol
        print("Starting Grabba MCP server (sse transport)...")
        asyncio.run(mcp.run_sse_async(
            host="0.0.0.0", 
            port=server_config.PORT, 
            path="/"
        ))

    else:
        if not server_config.API_KEY:
            raise ValueError("API Key required for stdio transport.")
        # Start the MCP server using StdioTransport
        print("Starting Grabba MCP server (stdio transport)...")
        asyncio.run(mcp.run_stdio_async())

if __name__ == "__main__":
    main()
