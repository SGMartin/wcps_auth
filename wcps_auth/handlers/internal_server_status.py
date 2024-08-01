from wcps_auth.handlers.base import PacketHandler


class GameServerStatusHandler(PacketHandler):
    async def process(self, server) -> None:
        ## Check if the server is authorized
        if server.authorized:
            server_time = self.get_block(1)
            server_id = self.get_block(2)
            current_players = self.get_block(3)
            current_rooms = self.get_block(4)

            ##TODO: Update more data
            server.current_players = int(current_players)
        else:
            logging.info(f"Ping from unauthorized server ignored")
            await server.disconnect()
