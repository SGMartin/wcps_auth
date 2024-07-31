import wcps_core.packets

class ClientXorKeys:
    SEND = 0x96
    RECEIVE = 0xC3

class PacketList:
    INTERNALGAMEAUTHENTICATION = wcps_core.packets.PacketList.GameServerAuthentication
    INTERNALGAMESTATUS = wcps_core.packets.PacketList.GameServerStatus
    INTERNALPLAYERAUTHENTICATION = wcps_core.packets.PacketList.ClientAuthentication
    LAUNCHER = 0x1010
    SERVER_LIST = 0x1100
    NICKNAME = 0x1101

class Launcher(wcps_core.packets.OutPacket):
    def __init__(self):
        super().__init__(packet_id=PacketList.LAUNCHER, xor_key=ClientXorKeys.SEND)
        self.fill(0, 7)

class ServerList(wcps_core.packets.OutPacket):
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
        if error_code != wcps_core.constants.ErrorCodes.SUCCESS or not u:
            self.append(error_code)
        else:
            self.append(1)
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

class InternalGameAuthentication(wcps_core.packets.OutPacket):
    def __init__(self, error_code, s=None):
        super().__init__(
            packet_id=PacketList.INTERNALGAMEAUTHENTICATION, 
            xor_key=wcps_core.constants.InternalKeys.XOR_AUTH_SEND)

        if error_code != wcps_core.constants.ErrorCodes.SUCCESS or not s:
            self.append(error_code)
        else:
            self.append(wcps_core.constants.ErrorCodes.SUCCESS)
            self.append(s.session_id) ## tell the server their session ID 
        
class InternalClientAuthentication(wcps_core.packets.OutPacket):
    def __init__(self, error_code, reported_user:str, reported_session:int, reported_rights:int):
        super().__init__(
            packet_id=PacketList.INTERNALPLAYERAUTHENTICATION,
            xor_key=wcps_core.constants.InternalKeys.XOR_AUTH_SEND
        )
        self.append(error_code)
        self.append(reported_user)
        self.append(reported_session)
        self.append(reported_rights)