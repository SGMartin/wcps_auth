import asyncio
import datetime
import socket
import time 
import threading

from networking import start_listeners
from networking import get_server_list

def run_async_listeners():
    asyncio.run(start_listeners())

def main():
    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    keep_running = True 

    print("Retrieving game server master list...")
    all_game_servers = get_server_list("root", "root", "auth_test")
    print(f"Found {len(all_game_servers)} server/s to watch.")

    async_listen_thread = threading.Thread(target = run_async_listeners)
    async_listen_thread.start()

    while(keep_running):
        print("Begin game server scan...")

        for server in all_game_servers:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((server.address, server.port))
            except:
                print(f"Failed to connect to {server.address}:{server.port}")
            finally:
                s.close()

        time.sleep(1)


if __name__ == '__main__':
    main()