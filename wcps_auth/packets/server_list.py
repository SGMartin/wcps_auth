from wcps_core.constants import ErrorCodes as corerr
from wcps_core.packets import OutPacket

from .packet_list import PacketList, ClientXorKeys

from sessions import SessionManager

class ServerList(OutPacket):
    class ErrorCodes:
        ILLEGAL_EXCEPTION = 70101
        NEW_NICKNAME = 72000
        WRONG_USER = 72010
        WRONG_PW = 72020
        ALREADY_LOGGED_IN = 72030
        CLIENT_VER_NOT_MATCH = 70301
        BANNED = 73050
        BANNED_TIME = 73020
        NOT_ACTIVE = 73040
        ENTER_ID_ERROR = 74010
        ENTER_PASSWORD_ERROR = 74020
        ERROR_NICKNAME = 74030
        NICKNAME_TAKEN = 74070
        NICKNAME_TOO_LONG = 74100
        ILLEGAL_NICKNAME = 74110

    def __init__(self, error_code: ErrorCodes, u=None):
        super().__init__(packet_id=PacketList.SERVER_LIST, xor_key=ClientXorKeys.SEND)
        if error_code != corerr.SUCCESS or not u:
            self.append(error_code)
        else:
            self.append(corerr.SUCCESS)
            self.append(1)  # ID
            self.append(0)  # unknown
            self.append(u.username)  # userid
            self.append("NULL")  # user PW. whatever is put here will be sent back if logged again
            self.append(u.displayname)
            self.append(u.session_id)  # current session ID
            self.append(0)  # unknown??? whatever is put here will be sent back if logged again
            self.append(0)  # unknown
            self.append(u.rights)  # rights
            self.append(1)  # Old servers say to append 1.11025 for PF20, but seems to be working atm.

            ## get all authorized servers
            session_manager = SessionManager()
            all_servers_sessions = session_manager.get_all_authorized_servers()

            # The 2008 client can handle up to 31 servers
            self.append(len(all_servers_sessions)) 

            for session in all_servers_sessions:
                s = session["server"] # Get the actual server 
                self.append(s.id)  # Server ID
                self.append(s.name)
                self.append(s.address)
                self.append(s.port)
                ## Current pop. Assumed to be x/3600. In the future, maybe
                ## do fractions for servers with smaller capacity
                self.append(s.current_players) 
                self.append(s.server_type)

            self.fill(-1, 4)  # ID?/NAME?/MASTER?/Unknown
            self.append(0)    # unknown
            self.append(0)  # unknown
