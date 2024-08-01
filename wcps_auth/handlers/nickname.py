from wcps_core.constants import ErrorCodes as corerr

from wcps_auth.database import displayname_exists, update_displayname
from wcps_auth.error_codes import ServerListError
from wcps_auth.handlers.base import PacketHandler
from wcps_auth.packets.packet_list import PacketList
from wcps_auth.packets.packet_factory import PacketFactory


class SetNickNameHandler(PacketHandler):
    async def process(self, user) -> None:
        if user.authorized:
            # WarRock won't let any user set a nickname longer than 16 char
            new_nickname = self.get_block(0)
            is_valid_nickname = False
            invalid_reason = None

            if not new_nickname.isalnum() or len(new_nickname) <= 3:
                invalid_reason = ServerListError.ILLEGAL_NICKNAME

            if len(new_nickname) > 16:
                invalid_reason = ServerListError.NICKNAME_TOO_LONG

            ## Database call to check if the display name is already in use
            if await displayname_exists(displayname=new_nickname):
                invalid_reason = ServerListError.NICKNAME_TAKEN
            else:
                is_valid_nickname = True

            if not is_valid_nickname:
                packet = PacketFactory.create_packet(
                    PacketList.SERVER_LIST, error_code=invalid_reason
                )
                await user.send(packet.build())
            else:
                await user.update_displayname(new_nickname=new_nickname)

                packet = PacketFactory.create_packet(
                    packet_id=PacketList.SERVER_LIST, error_code=corerr.SUCCESS, u=user
                )
                await user.send(packet.build())
                await user.disconnect()

                ## update the database nickname
                await update_displayname(
                    username=user.username, new_displayname=new_nickname
                )
