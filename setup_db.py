import asyncpg
import asyncio
import sys

async def create_database():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='postgres'
        )

        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'task_manager'"
        )
        
        if exists:
            print("Dropping existing database...")
            await conn.execute('DROP DATABASE IF EXISTS task_manager')
        
        print("Creating database 'task_manager'...")
        await conn.execute('CREATE DATABASE task_manager')
        print("Database 'task_manager' created successfully!")
        
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_database())
