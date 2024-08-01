from wcps_core.packets import OutPacket

from wcps_auth.packets.packet_list import PacketList, ClientXorKeys


class Launcher(OutPacket):
    def __init__(self):
        super().__init__(packet_id=PacketList.LAUNCHER, xor_key=ClientXorKeys.SEND)
        self.fill(0, 7)
