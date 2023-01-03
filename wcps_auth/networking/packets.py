from enum import Enum

from wcps_core.packets import OutPacket
from wcps_core import constants

import networking.users
import networking.servers


class ClientXorKeys:
    Send = 0x96
    Recieve = 0xC3


class PacketList:
    Launcher = 0x1010
    ServerList = 0x1100
    NickName = 0x1101
    Test = 0x1102


class Launcher(OutPacket):
    def __init__(self):
        super().__init__(packet_id=PacketList.Launcher, xor_key=ClientXorKeys.Send)
        self.fill(0, 7)


class ServerList(OutPacket):
    class ErrorCodes(Enum):
        IllegalException = 70101
        NewNickname = 72000
        WrongUser = 72010
        WrongPW = 72020
        AlreadyLoggedIn = 72030
        ClientVerNotMatch = 70301
        Banned = 73050
        BannedTime = 73020
        NotActive = 73040
        EnterIDError = 74010
        EnterPasswordError = 74020
        ErrorNickname = 74030
        NicknameTaken = 74070
        NicknameToLong = 74100
        IlligalNickname = 74110

    def __init__(self, error_code: ErrorCodes, u=None):
        super().__init__(packet_id=PacketList.ServerList, xor_key=ClientXorKeys.Send)
        if error_code != constants.ErrorCodes.SUCCESS or not u:
            self.append(error_code.value)
        else:
            self.append(1)
            self.append(1)  # ID
            self.append(0)  # unknown
            self.append(u.username)  # userid
            self.append("NULL")  # user PW. whatever is put here will be sent back if logged again
            self.append(u.displayname)
            self.append(u.session_id)  ## current session ID
            self.append(0)  # unknown??? whatever is put here will be sent back if logged again
            self.append(0)  # unknown
            self.append(u.rights)  # rights
            self.append(1)  # Olds servers say to append 1.11025 for PF20, but seems to be working atm.
            self.append(4)  ## Maximum value of servers for 2008 client is 31

            for i in range(0, 4):
                self.append(i)  # Server ID
                self.append(f"Test {i}")
                self.append("0.0.0.0.0")
                self.append("5340")
                self.append(100)
                self.append(1)

            self.fill(-1, 4) # unknown
            self.append(0) # unknown
            self.append(0) # unknown
