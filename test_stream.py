import asyncio
import json
import httpx

async def main():
    # First login or get token
    async with httpx.AsyncClient() as client:
        # Assuming admin/admin or test/test? Let's check db or simply create a token directly
        pass

if __name__ == "__main__":
    asyncio.run(main())
