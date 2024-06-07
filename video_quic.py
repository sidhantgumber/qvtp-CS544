import asyncio
from aioquic.asyncio import connect, serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived
from typing import Optional, Dict, Callable
from aioquic.tls import SessionTicket
import json
from collections import deque

from common import EchoQuicConnection, QuicStreamEvent
from quic_engine import EchoClientRequestHandler, EchoServerRequestHandler  # Use common.py

ALPN_PROTOCOL = "echo-protocol"

def build_server_quic_config(cert_file, key_file) -> QuicConfiguration:
    configuration = QuicConfiguration(
        alpn_protocols=[ALPN_PROTOCOL], 
        is_client=False
    )
    configuration.load_cert_chain(cert_file, key_file)
    return configuration

def build_client_quic_config(cert_file=None):
    configuration = QuicConfiguration(alpn_protocols=[ALPN_PROTOCOL], 
                                      is_client=True)
    if cert_file:
        configuration.load_verify_locations(cert_file)
    return configuration

def create_msg_payload(msg):
    return json.dumps(msg).encode('utf-8')

SERVER_MODE = 0
CLIENT_MODE = 1

class AsyncQuicServer(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._handlers: Dict[int, 'EchoServerRequestHandler'] = {}
        self._client_handler: Optional['EchoClientRequestHandler'] = None
        self._is_client: bool = self._quic.configuration.is_client
        self._mode: int = SERVER_MODE if not self._is_client else CLIENT_MODE
        if self._mode == CLIENT_MODE:
            self._attach_client_handler()

    def _attach_client_handler(self):
        if self._mode == CLIENT_MODE:
            from video_client import EchoClientRequestHandler  # Late import
            self._client_handler = EchoClientRequestHandler(
                authority=self._quic.configuration.server_name,
                connection=self._quic,
                protocol=self,
                scope={}
            )

    def remove_handler(self, stream_id):
        self._handlers.pop(stream_id, None)

    def quic_event_received(self, event):
        if self._mode == SERVER_MODE:
            self._quic_server_event_dispatch(event)
        else:
            self._quic_client_event_dispatch(event)

    def _quic_server_event_dispatch(self, event):
        if isinstance(event, StreamDataReceived):
            handler = self._handlers.get(event.stream_id)
            if handler is None:
                from video_server import EchoServerRequestHandler  # Late import
                handler = EchoServerRequestHandler(
                    authority=self._quic.configuration.server_name,
                    connection=self._quic,
                    protocol=self,
                    scope={},
                    stream_ended=event.end_stream,
                    stream_id=event.stream_id,
                    transmit=self.transmit
                )
                self._handlers[event.stream_id] = handler
                asyncio.ensure_future(handler.launch_qvtp())
            handler.quic_event_received(event)

    def _quic_client_event_dispatch(self, event):
        if isinstance(event, StreamDataReceived):
            self._client_handler.quic_event_received(event)

class SessionTicketStore:
    def __init__(self) -> None:
        self.tickets: Dict[bytes, SessionTicket] = {}

    def add(self, ticket: SessionTicket) -> None:
        self.tickets[ticket.ticket] = ticket

    def pop(self, label: bytes) -> Optional[SessionTicket]:
        return self.tickets.pop(label, None)

async def run_server(server, server_port, configuration):  
    print("[svr] Server starting...")  
    await serve(server, server_port, configuration=configuration, 
                create_protocol=AsyncQuicServer,
                session_ticket_fetcher=SessionTicketStore().pop,
                session_ticket_handler=SessionTicketStore().add)
    await asyncio.Future()

async def run_client(server, server_port, configuration, video_path, download):    
    async with connect(server, server_port, configuration=configuration, create_protocol=AsyncQuicServer) as client:
        await client._client_handler.launch_qvtp(video_path, download)
