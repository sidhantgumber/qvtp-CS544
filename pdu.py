import struct
import hashlib

MSG_TYPE_REQUEST = 1
MSG_TYPE_RESPONSE = 2
MSG_TYPE_DATA = 3
MSG_TYPE_ACK = 4
MSG_TYPE_ERROR = 5

class Datagram:
    def __init__(self, mtype, msg, filename="", filesize=0, transaction_id=0, sequence_num=0, data=b'', checksum=''):
        self.mtype = mtype
        self.msg = msg
        self.filename = filename
        self.filesize = filesize
        self.transaction_id = transaction_id
        self.sequence_num = sequence_num
        self.data = data
        self.checksum = checksum

    def to_bytes(self):
        header = struct.pack('!I', self.mtype) + struct.pack('!I', len(self.msg)) + self.msg.encode('utf-8')
        if self.mtype in [MSG_TYPE_REQUEST, MSG_TYPE_RESPONSE, MSG_TYPE_DATA]:
            header += struct.pack('!I', len(self.filename)) + self.filename.encode('utf-8')
            header += struct.pack('!Q', self.filesize)
            header += struct.pack('!I', self.transaction_id)
            header += struct.pack('!I', self.sequence_num)
            header += struct.pack('!I', len(self.data)) + self.data
            header += self.checksum.encode('utf-8')
        return header

    @classmethod
    def from_bytes(cls, data):
        mtype = struct.unpack('!I', data[:4])[0]
        msg_len = struct.unpack('!I', data[4:8])[0]
        msg = data[8:8+msg_len].decode('utf-8')
        index = 8 + msg_len
        filename_len = struct.unpack('!I', data[index:index+4])[0]
        index += 4
        filename = data[index:index+filename_len].decode('utf-8')
        index += filename_len
        filesize = struct.unpack('!Q', data[index:index+8])[0]
        index += 8
        transaction_id = struct.unpack('!I', data[index:index+4])[0]
        index += 4
        sequence_num = struct.unpack('!I', data[index:index+4])[0]
        index += 4
        data_len = struct.unpack('!I', data[index:index+4])[0]
        index += 4
        payload = data[index:index+data_len]
        index += data_len
        checksum = data[index:].decode('utf-8')
        return cls(mtype, msg, filename, filesize, transaction_id, sequence_num, payload, checksum)

    def calculate_checksum(self):
        hash_md5 = hashlib.md5()
        hash_md5.update(self.data)
        self.checksum = hash_md5.hexdigest()

    def is_checksum_valid(self):
        if not self.checksum:
            return False
        hash_md5 = hashlib.md5()
        hash_md5.update(self.data)
        return self.checksum == hash_md5.hexdigest()
