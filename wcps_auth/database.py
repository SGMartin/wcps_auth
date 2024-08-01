import asyncio
import aiomysql

from wcps_auth.config import settings

pool = None


async def create_pool():
    global pool
    pool = await aiomysql.create_pool(
        host=settings().server_ip,
        port=settings().database_port,
        user=settings().database_user,
        password=settings().database_password,
        db=settings().database_name,
        loop=asyncio.get_event_loop(),
    )
    return pool


async def run_pool():
    await create_pool()


def generate_servers_addresses(query_results: list) -> list:
    server_list = []
    for candidate_server in query_results:
        ## Each result is a tuple of 4 fields
        server_id, addr, port, active = candidate_server
        server_list.append((server_id, addr, port))

    return server_list


async def get_server_list() -> list:
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute("SELECT * FROM servers WHERE active = 1")
            results = await cur.fetchall()
            server_list = generate_servers_addresses(results)
            return server_list


async def get_user_details(user_id: str) -> dict:
    async with pool.acquire() as connection:
        await connection.select_db("auth_test")
        async with connection.cursor() as cur:
            query = "SELECT * FROM users WHERE username = %s"
            await cur.execute(query, (user_id,))
            user_details = await cur.fetchall()
            # By default a tuple is recieved
            if user_details:
                user_details = user_details[0]
                if len(user_details) == 6:
                    this_user = {
                        "id": int(user_details[0]),
                        "username": user_details[1],
                        "displayname": user_details[2],
                        "password": user_details[3],
                        "salt": user_details[4],
                        "rights": int(user_details[5]),
                    }
                    return this_user
                else:
                    # TODO: Improper db format
                    print("Improper database schema")
                    return None
            else:
                return None


async def displayname_exists(displayname):
    async with pool.acquire() as connection:
        await connection.select_db("auth_test")
        async with connection.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM users WHERE displayname=%s", (displayname,))
            (count,) = await cur.fetchone()
            return count > 0


async def update_displayname(username, new_displayname):
    async with pool.acquire() as connection:
        await connection.select_db("auth_test")
        async with connection.cursor() as cur:
            # Update the displayname securely using a parameterized query
            query = "UPDATE users SET displayname=%s WHERE username=%s"
            await cur.execute(query, (new_displayname, username))
            await connection.commit()
            return True