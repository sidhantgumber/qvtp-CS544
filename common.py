class QuicStreamEvent:
    def __init__(self, stream_id: int, data: bytes, end_stream: bool):
        self.stream_id = stream_id
        self.data = data
        self.end_stream = end_stream

class EchoQuicConnection:
    def __init__(self, send=None, receive=None, close=None, get_next_stream_id=None):
        self.send = send
        self.receive = receive
        self.close = close
        self.get_next_stream_id = get_next_stream_id
        self._connections = []

    def new_stream(self):
        # Create a new stream and return its ID
        stream_id = len(self._connections)
        self._connections.append(stream_id)
        return stream_id

    async def send(self, event: QuicStreamEvent):
        # Simulate sending a QUIC stream event
        pass

    async def receive(self) -> QuicStreamEvent:
        # Simulate receiving a QUIC stream event
        pass
