from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket

from wcps_auth.packets.packet_list import PacketList, ClientXorKeys

from wcps_auth.sessions import SessionManager
from wcps_auth.error_codes import ServerListError


class ServerList(OutPacket):
    def __init__(self, error_code: ServerListError, u=None):
        super().__init__(packet_id=PacketList.SERVER_LIST, xor_key=ClientXorKeys.SEND)
        if error_code != corerr.SUCCESS or not u:
            self.append(error_code)
        else:
            self.append(corerr.SUCCESS)
            self.append(1)  # ID
            self.append(0)  # unknown
            self.append(u.username)  # userid
            self.append(
                "NULL"
            )  # user PW. whatever is put here will be sent back if logged again
            self.append(u.displayname)
            self.append(u.session_id)  # current session ID
            self.append(
                0
            )  # unknown??? whatever is put here will be sent back if logged again
            self.append(0)  # unknown
            self.append(u.rights)  # rights
            self.append(
                1
            )  # Old servers say to append 1.11025 for PF20, but seems to be working atm.

            ## get all authorized servers
            session_manager = SessionManager()
            all_servers_sessions = session_manager.get_all_authorized_servers()

            # The 2008 client can handle up to 31 servers
            self.append(len(all_servers_sessions))

            for session in all_servers_sessions:
                s = session["server"]  # Get the actual server
                self.append(s.id)  # Server ID
                self.append(s.name)
                self.append(s.address)
                self.append(s.port)
                ## Current pop. Assumed to be x/3600. In the future, maybe
                ## do fractions for servers with smaller capacity
                self.append(s.current_players)
                self.append(s.server_type)

            self.fill(-1, 4)  # ID?/NAME?/MASTER?/Unknown
            self.append(0)  # unknown
            self.append(0)  # unknown
