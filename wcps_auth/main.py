import asyncio
import datetime
import time 
import threading

from networking import get_server_list, get_servers_details, start_user_listener

import asyncio, socket

def main():
    # Get the current date
    now = datetime.datetime.now()
    start_time = now.strftime("%d/%m/%Y")
    keep_running = True 

    print(f"Authorization server started on {start_time}")
    print(f"Fetching list of active servers...")

    game_servers = get_server_list("root","root","auth_test")

    print(f"Found {len(game_servers)} server/s in the database.")
    print("Begin listening for clients...")
    client_listener_thread = threading.Thread(target=start_user_listener)
    client_listener_thread.start()
    
    while(keep_running):
        print("Querying server list for online game servers...")
        game_server_updater = threading.Thread(target = get_servers_details, args = [game_servers])
        game_server_updater.start()
  
        for server in game_servers:
            if server.is_online:
                print(f"Server is online with {server.current_players} current players")

        time.sleep(30)



if __name__ == '__main__':
    main()