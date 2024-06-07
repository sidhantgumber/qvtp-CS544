import asyncio
import os
from typing import Dict
from common import EchoQuicConnection, QuicStreamEvent
import pdu

class EchoClientRequestHandler:
    def __init__(self, connection):
        self.connection = connection

    async def launch_qvtp(self, video_path: str, download: bool):
        if download:
            await download_video({}, self.connection, video_path)
        else:
            await upload_video({}, self.connection, video_path)

async def upload_video(scope: Dict, conn: EchoQuicConnection, filepath: str):
    print('[cli] uploading video:', filepath)
    
    # Open the video file
    with open(filepath, 'rb') as f:
        video_data = f.read()
    
    filesize = len(video_data)
    print(f'[cli] Read file: {filepath}, Size: {filesize}')
    
    # Create and send the REQUEST message to initiate the upload
    request_msg = pdu.Datagram(pdu.MSG_TYPE_REQUEST, "", filename=os.path.basename(filepath), filesize=filesize)
    new_stream_id = conn.new_stream()
    qs = QuicStreamEvent(new_stream_id, request_msg.to_bytes(), False)
    print(f'[cli] Sending REQUEST')
    await conn.send(qs)
    
    # Wait for the RESPONSE from the server
    try:
        response: QuicStreamEvent = await conn.receive()
        print('[cli] Response received')
    except Exception as e:
        print(f'[cli] Error receiving response: {e}')
        return
    response_msg = pdu.Datagram.from_bytes(response.data)
    print(f'[cli] Server response received')
    
    if response_msg.mtype == pdu.MSG_TYPE_RESPONSE:
        # Send the video data in chunks
        chunk_size = 10 * 1024  # 100 KB chunks
        num_chunks = (filesize + chunk_size - 1) // chunk_size
        print(f'[cli] Total chunks to send: {num_chunks}')
        
        for i in range(0, filesize, chunk_size):
            chunk_data = video_data[i:i + chunk_size]
            data_msg = pdu.Datagram(pdu.MSG_TYPE_DATA, "", sequence_num=i // chunk_size + 1, data=chunk_data)
            data_msg.calculate_checksum()
            print(f'[cli] Sending DATA chunk: {i // chunk_size + 1}/{num_chunks}, Size: {len(chunk_data)}')
            await conn.send(QuicStreamEvent(new_stream_id, data_msg.to_bytes(), False))
        
        # Send an end-of-stream signal
        print('[cli] Sending end-of-stream signal')
        await conn.send(QuicStreamEvent(new_stream_id, b'', True))
        print('[cli] End-of-stream signal sent')
    
    print('[cli] Upload complete')

async def download_video(scope: Dict, conn: EchoQuicConnection, filename: str):
    print('[cli] downloading video:', filename)
    
    # Create and send the REQUEST message to initiate the download
    request_msg = pdu.Datagram(pdu.MSG_TYPE_REQUEST, "", filename=filename)
    new_stream_id = conn.new_stream()
    qs = QuicStreamEvent(new_stream_id, request_msg.to_bytes(), False)
    print(f'[cli] Sending REQUEST')
    await conn.send(qs)
    
    # Wait for the RESPONSE from the server
    response: QuicStreamEvent = await conn.receive()
    response_msg = pdu.Datagram.from_bytes(response.data)
    print(f'[cli] Server response received')
    
    if response_msg.mtype == pdu.MSG_TYPE_RESPONSE:
        # Receive the video data in chunks
        with open(filename, 'wb') as f:
            while True:
                message: QuicStreamEvent = await conn.receive()
                if message.end_stream:
                    break
                data_msg = pdu.Datagram.from_bytes(message.data)
                if data_msg.is_checksum_valid():
                    f.write(data_msg.data)
                    print(f'[cli] Received DATA chunk, Size: {len(data_msg.data)}')
                else:
                    print('[cli] Checksum invalid. Data integrity compromised.')
    
    print('[cli] Download complete')

async def echo_client_proto(scope: Dict, conn: EchoQuicConnection, video_path: str, download: bool):
    if download:
        await download_video(scope, conn, video_path)
    else:
        await upload_video(scope, conn, video_path)

async def start_client():
    scope = {}  # This would be your actual QUIC connection scope
    conn = EchoQuicConnection()  # This would be your actual QUIC connection object
    await echo_client_proto(scope, conn, "testvideo.mp4", False)

if __name__ == "__main__":
    asyncio.run(start_client())
