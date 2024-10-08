import asyncio
import logging

from wcps_core.packets import PacketBuffer, Connection


class BaseNetworkEntity:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        xor_key_send,
        xor_key_receive,
    ):
        self.reader = reader
        self.writer = writer
        self.xor_key_send = xor_key_send
        self.xor_key_receive = xor_key_receive
        self.authorized = False
        self.session_id = -1

        self._connection = Connection(xor_key=self.xor_key_send).build()
        asyncio.create_task(self.send(self._connection))
        asyncio.create_task(self.listen())

    async def listen(self):
        while True:
            data = await self.reader.read(1024)
            if not data:
                await self.disconnect()
                break

            try:
                incoming_packets = PacketBuffer(
                    buffer=data, receptor=self, xor_key=self.xor_key_receive
                )
                if incoming_packets.decoded_buffer:
                    logging.info(f"BUFFER IN:: {incoming_packets.decoded_buffer}")

                    for packet in incoming_packets.packet_stack:
                        handler = self.get_handler_for_packet(packet.packet_id)
                        if handler:
                            asyncio.create_task(handler.handle(packet))
                        else:
                            logging.error(
                                f"Unknown handler for packet {packet.packet_id}"
                            )
                else:
                    logging.error(f"Cannot decrypt packet buffer {incoming_packets}")
                    await self.disconnect()
            except Exception as e:
                logging.exception(f"Error processing packet: {e}")
                await self.disconnect()
                break

    async def send(self, buffer):
        try:
            self.writer.write(buffer)
            await self.writer.drain()
        except Exception as e:
            logging.exception(f"Error sending packet: {e}")
            await self.disconnect()

    async def disconnect(self):
        self.writer.close()

    def get_handler_for_packet(self, packet_id: int):
        raise NotImplementedError("Subclasses must implement this method.")
