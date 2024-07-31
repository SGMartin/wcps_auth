from wcps_auth.packets.packet_list import PacketList

from wcps_auth.packets.launcher import Launcher
from wcps_auth.packets.server_list import ServerList
from wcps_auth.packets.internal_game_auth import InternalGameAuthentication
from wcps_auth.packets.internal_user_auth import InternalClientAuthentication

class PacketFactory:
    packet_classes = {
        PacketList.LAUNCHER: Launcher,
        PacketList.SERVER_LIST: ServerList,
        PacketList.INTERNALGAMEAUTHENTICATION: InternalGameAuthentication,
        PacketList.INTERNALPLAYERAUTHENTICATION: InternalClientAuthentication,
    }

    @staticmethod
    def create_packet(packet_id: int, *args, **kwargs):
        packet_class = PacketFactory.packet_classes.get(packet_id)
        if packet_class:
            return packet_class(*args, **kwargs)
        else:
            raise ValueError(f"Unknown packet ID: {packet_id}")

    @staticmethod
    def get_packet_class(packet_id: int):
        return PacketFactory.packet_classes.get(packet_id)

    @staticmethod
    def get_packet_id(packet_class):
        for packet_id, cls in PacketFactory.packet_classes.items():
            if cls == packet_class:
                return packet_id
        return None