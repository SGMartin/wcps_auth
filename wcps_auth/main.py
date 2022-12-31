import asyncio
import datetime
import socket
import time 
import threading

#from networking import get_server_list, get_servers_details, start_user_listener

from networking import client_listener,  server_listener, get_server_list

# Start the game server listener in its own thread
def start_server_listener():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server_listener())


# Start the client listener in its own thread
def start_client_listener():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client_listener())


def main():
    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    keep_running = True 

    print("Client listener started.")
    user_listener_thread = threading.Thread(target = start_client_listener)
    user_listener_thread.start()

    print("Game server listener started.")
    server_listener_thread = threading.Thread(target = start_server_listener)
    server_listener_thread.start()

    print("Retrieving game server master list...")
    all_game_servers = get_server_list("root", "root", "auth_test")
    print(f"Found {len(all_game_servers)} server/s to watch.")

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

        time.sleep(10)


if __name__ == '__main__':
    main()