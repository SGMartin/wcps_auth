import unittest
from unittest.mock import MagicMock, patch
import asyncio
from wcps_core.packets import InPacket
from wcps_auth.entities import BaseNetworkEntity

class TestBaseNetworkEntity(unittest.TestCase):

    def setUp(self):
        self.reader = MagicMock()
        self.writer = MagicMock()
        self.xor_key_send = bytes([0x96])  # Corrected to bytes
        self.xor_key_receive = bytes([0xc3])  # Corrected to bytes

    async def create_entity(self):
        # This method runs in an event loop and can create async tasks
        self.entity = BaseNetworkEntity(self.reader, self.writer, self.xor_key_send, self.xor_key_receive)
        await asyncio.sleep(0.1)  # Give async tasks time to complete if necessary

    async def test_listen_processes_data(self):
        with patch('wcps_auth.entities.logging'):
            with patch('wcps_core.packets.InPacket', autospec=True) as MockInPacket:
                MockInPacket.return_value.decoded_buffer = b'decoded_data'
                MockInPacket.return_value.packet_id = 1
                self.entity.get_handler_for_packet = MagicMock(return_value=MagicMock())

                self.reader.read = asyncio.coroutine(lambda n: b'some_data')
                self.reader.read.return_value = b'some_data'

                await self.create_entity()  # Create the entity with running event loop
                await asyncio.sleep(0.1)  # Allow async tasks to run

                self.entity.get_handler_for_packet.assert_called_with(1)
                self.entity.get_handler_for_packet.return_value.handle.assert_called_with(MockInPacket.return_value)

    async def test_send_success(self):
        with patch('wcps_auth.entities.logging'):
            self.writer.drain = asyncio.coroutine(lambda: None)
            await self.create_entity()  # Create the entity with running event loop
            await self.entity.send(b'some_buffer')
            self.writer.write.assert_called_with(b'some_buffer')

    async def test_send_failure(self):
        with patch('wcps_auth.entities.logging'):
            self.writer.drain = asyncio.coroutine(lambda: None)
            self.writer.write.side_effect = Exception("Write failed")
            await self.create_entity()  # Create the entity with running event loop
            try:
                await self.entity.send(b'some_buffer')
            except Exception:
                pass
            self.assertTrue(self.writer.close.called)

    async def test_disconnect(self):
        with patch('wcps_auth.entities.logging'):
            await self.create_entity()  # Create the entity with running event loop
            await self.entity.disconnect()
            self.writer.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
