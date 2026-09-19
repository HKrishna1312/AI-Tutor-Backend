
import asyncio

from app.services.chat_service import generate_resume_answer


async def main():

    result = await asyncio.to_thread(
        generate_resume_answer,
        question="What skills are mentioned in my resume?",
        user_id="5"
    )

    print("\nANSWER:")
    print(result["answer"])

    print("\nSOURCES:")
    for source in result["sources"]:
        print(source["filename"])


if __name__ == "__main__":
    asyncio.run(main())