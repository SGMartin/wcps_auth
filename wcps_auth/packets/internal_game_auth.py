from wcps_core.constants import ErrorCodes, InternalKeys
from wcps_core.packets import OutPacket

from wcps_auth.packets.packet_list import PacketList

class InternalGameAuthentication(OutPacket):
    def __init__(self, error_code, s=None):
        super().__init__(
            packet_id=PacketList.INTERNALGAMEAUTHENTICATION, 
            xor_key=InternalKeys.XOR_AUTH_SEND)

        if error_code != ErrorCodes.SUCCESS or not s:
            self.append(error_code)
        else:
            self.append(ErrorCodes.SUCCESS)
            self.append(s.session_id) ## tell the server their session ID 