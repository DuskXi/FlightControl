from loguru import logger

from RadioCommunication.drone import RadioConnector
from RadioCommunication.datapacket import DataPacket


def main():
    packet = DataPacket()
    buffer = b''
    encoded = packet.encode(r'11451\41\91\98\10 cnm nmsl sb fuck F:\Minecraft Server\1.7.10 cnm 苏卡不列 下北泽 1919810'.encode("utf-8"))
    logger.debug(f"原始数据大小: [{encoded[0][0]}], 转义后大小: [{encoded[1][0]}]")
    buffer += encoded[2][0]
    encoded = packet.encode(r'第二段'.encode("utf-8"))
    logger.debug(f"原始数据大小: [{encoded[0][0]}], 转义后大小: [{encoded[1][0]}]")
    buffer += encoded[2][0]
    decodedArray = packet.decode(buffer)
    for decoded in decodedArray:
        logger.debug(f"解码结果: [{decoded.decode('utf-8')}]")


if __name__ == "__main__":
    print()
    main()
