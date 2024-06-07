import asyncio
from typing import Dict
from common import EchoQuicConnection, QuicStreamEvent
import pdu

async def handle_upload(scope: Dict, conn: EchoQuicConnection, initial_msg: pdu.Datagram):
    print('[svr] handling upload for:', initial_msg.filename)
    
    # Send a RESPONSE message to the client to acknowledge the upload request
    response_msg = pdu.Datagram(pdu.MSG_TYPE_RESPONSE, "", filename=initial_msg.filename, filesize=initial_msg.filesize)
    print(f'[svr] Sending RESPONSE')
    await conn.send(QuicStreamEvent(initial_msg.transaction_id, response_msg.to_bytes(), False))
    
    # Open a new file to write the incoming video data
    file_path = f"received_{initial_msg.filename}"
    with open(file_path, 'wb') as f:
        total_chunks = 0
        total_size = 0
        last_sequence_num = 0
        while True:
            try:
                print('[svr] Waiting to receive data chunks...')
                message: QuicStreamEvent = await conn.receive()
                print(f'[svr] Received message: {message}')
                if message.end_stream:
                    print('[svr] End-of-stream signal received')
                    break
                if message.data:
                    data_msg = pdu.Datagram.from_bytes(message.data)
                    if data_msg.is_checksum_valid():
                        if data_msg.sequence_num == last_sequence_num + 1:
                            f.write(data_msg.data)
                            total_size += len(data_msg.data)
                            total_chunks += 1
                            last_sequence_num = data_msg.sequence_num
                            print(f'[svr] Received DATA chunk {total_chunks}, Size: {len(data_msg.data)}')
                        else:
                            print(f'[svr] Out of order packet received: {data_msg.sequence_num} expected: {last_sequence_num + 1}')
                            # Handle out-of-order packets if necessary
                    else:
                        print('[svr] Checksum invalid. Data integrity compromised.')
                else:
                    print('[svr] Received empty data message')
            except Exception as e:
                print(f'[svr] Error receiving data: {e}')
                break
    
    print(f'[svr] Upload complete for: {initial_msg.filename}. Total size: {total_size} bytes in {total_chunks} chunks.')
    # Send an ACK message to the client
    ack_msg = pdu.Datagram(pdu.MSG_TYPE_ACK, "Upload complete")
    print(f'[svr] Sending ACK')
    await conn.send(QuicStreamEvent(initial_msg.transaction_id, ack_msg.to_bytes(), True))

async def handle_download(scope: Dict, conn: EchoQuicConnection, initial_msg: pdu.Datagram):
    print('[svr] handling download for:', initial_msg.filename)
    
    # Open the requested video file
    try:
        with open(initial_msg.filename, 'rb') as f:
            video_data = f.read()
        
        filesize = len(video_data)
        print(f'[svr] Read file: {initial_msg.filename}, Size: {filesize}')
        
        # Send a RESPONSE message to the client
        response_msg = pdu.Datagram(pdu.MSG_TYPE_RESPONSE, "", filename=initial_msg.filename, filesize=filesize)
        print(f'[svr] Sending RESPONSE')
        await conn.send(QuicStreamEvent(initial_msg.transaction_id, response_msg.to_bytes(), False))
        
        # Send the video data in chunks
        chunk_size = 10 * 1024  # 100 KB chunks
        num_chunks = (filesize + chunk_size - 1) // chunk_size
        print(f'[svr] Total chunks to send: {num_chunks}')
        
        for i in range(0, filesize, chunk_size):
            chunk_data = video_data[i:i + chunk_size]
            data_msg = pdu.Datagram(pdu.MSG_TYPE_DATA, "", sequence_num=i // chunk_size + 1, data=chunk_data)
            data_msg.calculate_checksum()
            await conn.send(QuicStreamEvent(initial_msg.transaction_id, data_msg.to_bytes(), False))
            print(f'[svr] Sending DATA chunk: {i // chunk_size + 1}/{num_chunks}, Size: {len(chunk_data)}')
        
        # Send an end-of-stream signal
        await conn.send(QuicStreamEvent(initial_msg.transaction_id, b'', True))
        print('[svr] End-of-stream signal sent')
        
    except FileNotFoundError:
        # Send an ERROR message to the client
        error_msg = pdu.Datagram(pdu.MSG_TYPE_ERROR, "File not found")
        print(f'[svr] Sending ERROR')
        await conn.send(QuicStreamEvent(initial_msg.transaction_id, error_msg.to_bytes(), False))

async def echo_server_proto(scope: Dict, conn: EchoQuicConnection):
    print("[svr] Waiting for messages...")
    while True:
        try:
            message: QuicStreamEvent = await conn.receive()
            print(f"[svr] received message")
            initial_msg = pdu.Datagram.from_bytes(message.data)
            print(f"[svr] parsed message")
            
            if initial_msg.mtype == pdu.MSG_TYPE_REQUEST:
                if initial_msg.filename:
                    if initial_msg.filesize > 0:
                        print(f'[svr] Received upload request for file: {initial_msg.filename} with size: {initial_msg.filesize}')
                        await handle_upload(scope, conn, initial_msg)
                    else:
                        print(f'[svr] Received download request for file: {initial_msg.filename}')
                        await handle_download(scope, conn, initial_msg)
                else:
                    error_msg = pdu.Datagram(pdu.MSG_TYPE_ERROR, "Invalid request")
                    print(f'[svr] Sending ERROR')
                    await conn.send(QuicStreamEvent(message.stream_id, error_msg.to_bytes(), False))
        except Exception as e:
            print(f'[svr] Error receiving initial message: {e}')
            break

async def start_server():
    scope = {}  # This would be your actual QUIC connection scope
    conn = EchoQuicConnection()  # This would be your actual QUIC connection object
    await echo_server_proto(scope, conn)

if __name__ == "__main__":
    asyncio.run(start_server())
