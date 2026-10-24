
import asyncio
import logging

from app.services.indeed_job_service import indeed_job_service

logging.basicConfig(level=logging.INFO)


async def main():
    result = await indeed_job_service.search_jobs(
        keyword="Python AI Engineer",
        location="Bengaluru",
        country="India",
    )

    print("Status:", result["status"])
    print("Count:", result["count"])

    for job in result["jobs"]:
        print(job)


if __name__ == "__main__":
    asyncio.run(main())
