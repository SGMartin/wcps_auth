import asyncio
import aiomysql

pool = None

async def create_pool():
    global pool
    pool = await aiomysql.create_pool(
        host='localhost',
        port=3306,
        user='root',
        password='root',
        db='auth_test',
        loop=asyncio.get_event_loop()
    )
    return pool

async def run_pool():
    await create_pool()


def generate_servers_addresses(query_results: list) -> list:
    server_list = []
    for candidate_server in query_results:
        ## Each result is a tuple of 4 fields
        server_id, addr, port, active = candidate_server
        server_list.append((addr, port))

    return server_list


async def get_server_list() -> list:
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute("SELECT * FROM servers WHERE active = 1")
            results = await cur.fetchall()
            server_list = generate_servers_addresses(results)
            return server_list


async def get_user_details(user_id:str) -> dict:
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            query = "SELECT * FROM users WHERE username = ?"
            this_user = await cur.execute(query, (user_id,))
            print(this_user)