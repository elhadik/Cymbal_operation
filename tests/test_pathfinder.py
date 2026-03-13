import asyncio
from agents.pathfinder_agent import run_pathfinder
import os
from dotenv import load_dotenv

load_dotenv()
async def main():
    try:
        res = await run_pathfinder()
        print("RESULT:")
        print(res)
    except Exception as e:
        print("EXCEPTION:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
