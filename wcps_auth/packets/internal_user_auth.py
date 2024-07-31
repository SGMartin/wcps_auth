from wcps_core.constants import ErrorCodes, InternalKeys
from wcps_core.packets import OutPacket

from wcps_auth.packets.packet_list import PacketList

class InternalClientAuthentication(OutPacket):
    def __init__(self, error_code: ErrorCodes, reported_user:str, reported_session:int, reported_rights:int):
        super().__init__(
            packet_id=PacketList.INTERNALPLAYERAUTHENTICATION,
            xor_key=InternalKeys.XOR_AUTH_SEND
        )
        self.append(error_code)
        self.append(reported_user)
        self.append(reported_session)
        self.append(reported_rights)