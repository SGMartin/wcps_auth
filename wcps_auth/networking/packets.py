from wcps_core.packets import OutPacket


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
