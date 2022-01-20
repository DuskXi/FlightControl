import zlib
import numpy as np


class DataPacket:
    escapeChar: bytes = b'\\'

    def __init__(self, compressed=False):
        self.compressed = compressed
        self.decompressObject = None
        self.buffer = b''
        self.bufferIndex = 0
        self.isRun = True

    def resetDecompressObject(self):
        if self.decompressObject is not None:
            self.decompressObject.flush()
        self.decompressObject = zlib.decompressobj()

    def decode(self, data: bytes):
        """
        数据包解码

        该函数将会把bytes流存入缓冲区, 并在缓冲区中查找合法的数据包头

        如果找到合法的数据包头, 则将缓冲区中的数据包头和数据包数据分离, 从缓冲区中删除已解析数据包并返回(但是缓冲区中未解析的数据包还会保留)

        如果解析数据包头后发现缓冲区中数据长度还未达到数据包长度, 并且未出现非法转义符(没有被转义的转义符), 则会返回 True

        如果解析过程中在数据长度未达到数据包长度之前发现了未被转义的转义符(这意味着出现了包头), 表明发生了丢包, 则调用函数寻找下一个合法的数据包头, 丢弃无效数据, 并返回 False

        如若数据本身就不以合法的包头结构开始, 则调用函数寻找下一个合法包头, 丢弃无效数据, 并返回 False

        :param data: 数据流
        :return: bytes数据: 成功解析数据包 , True: 等待数据包结束, False: 发生丢包, 清除了无效数据
        """
        self.buffer += data
        escapeChar = DataPacket.escapeChar[0]
        if len(self.buffer) > self.bufferIndex:
            if self.buffer[0] == escapeChar and len(self.buffer) > 5:
                arraySize: bytes = self.buffer[1:5]
                if len(list(filter(lambda x: b'0'[0] <= x <= b'9'[0], arraySize))) == 4:
                    packageSize: int = int(arraySize.decode("ascii"))
                    if self.bufferIndex < 5:
                        # 如果index小于5, 则设置为5, 因为后续的寻找规则不允许从包头开始搜索, 因为包头已经被正确解析
                        self.bufferIndex = 5
                    i = self.bufferIndex
                    # for i in range(self.bufferIndex, len(self.buffer)):
                    while i < len(self.buffer):
                        self.bufferIndex = i
                        if self.buffer[i] == escapeChar and i != len(self.buffer) - 1:
                            if self.buffer[i + 1] == escapeChar:
                                i += 2
                                continue
                            else:
                                if i - 5 == packageSize:
                                    # 数据包完整
                                    # 截取包内容, 返回将转义符替换后的内容
                                    # 从缓存中移除已解析的数据包
                                    resultData = [self.buffer[5:i].replace(DataPacket.escapeChar + DataPacket.escapeChar, DataPacket.escapeChar)]
                                    self.buffer = self.buffer[i:]
                                    self.bufferIndex = 0
                                    if len(self.buffer) > 5:
                                        resultRemainData = self.decode(b'')
                                        if type(resultRemainData) != bool:
                                            resultData += resultRemainData
                                    return resultData
                                else:
                                    # 数据包不完整
                                    # 丢弃所有数据
                                    self.buffer = self.buffer[i + 1:]
                                    self.bufferIndex = 0
                                    return False
                        elif i + 1 - 5 == packageSize:
                            # 截取包内容, 返回将转义符替换后的内容
                            # 从缓存中移除已解析的数据包
                            resultData = [self.buffer[5:i + 1].replace(DataPacket.escapeChar + DataPacket.escapeChar, DataPacket.escapeChar)]
                            self.buffer = self.buffer[i + 1:]
                            self.bufferIndex = 0
                            if len(self.buffer) > 5:
                                resultRemainData = self.decode(b'')
                                if type(resultRemainData) != bool:
                                    resultData += resultRemainData
                            return resultData
                        i += 1

                else:
                    # 包头字符不合法(有不为数字的字符出现在包头位), 进入数据丢弃过程
                    # 寻找下一个合法的数据包头
                    result = self.findValidPackageHead()
                    if result is False:
                        # 数据包头未找到
                        # 丢弃所有数据, 仅保留最后一个字符
                        self.buffer = self.buffer[-1]
                        self.bufferIndex = 0
                    else:
                        # 数据包头已找到
                        # 丢弃所有合法包头之前数据
                        self.buffer = self.buffer[result:]
                        self.bufferIndex = 0
                    return False
            elif self.buffer[0] != escapeChar:
                # 包头字符不合法(第一个字符不为转义字符), 进入数据丢弃过程
                # 寻找下一个合法的数据包头
                result = self.findValidPackageHead()
                if result is False:
                    # 数据包头未找到
                    # 丢弃所有数据, 仅保留最后一个字符
                    self.buffer = self.buffer[-1]
                    self.bufferIndex = 0
                else:
                    # 数据包头已找到
                    # 丢弃所有合法包头之前数据
                    self.buffer = self.buffer[result:]
                    self.bufferIndex = 0
                return False
        return True

    def findValidPackageHead(self):
        """
        寻找下一个合法的数据包头
        :return:
        """
        escapeChar = DataPacket.escapeChar[0]
        for i in range(self.bufferIndex, len(self.buffer)):
            if self.buffer[i] == escapeChar:
                # 判断是否为缓冲的最后一个字符
                if i != len(self.buffer) - 1:
                    # 如果不是最后一个字符, 判断下一个字符是否为转义符
                    if self.buffer[i + 1] == escapeChar:
                        # 如果是转义符, 则继续查找
                        continue
                    else:
                        # 如果转义符后一位不是转义符, 则说明数据包头已经找到
                        arraySize = self.buffer[i + 1: i + 5]
                        # 判断数据包长度数据是否合法(是否全为数字)
                        if len(list(filter(lambda x: b'0'[0] <= x <= b'9'[0], arraySize))) == 4:
                            # 则数据包长度已找到(返回值从转义符开始)
                            return i
                        else:
                            # 否则继续向后查找
                            continue
                else:
                    # 如果是最后一个字符, 则表明下一个合法的数据包头还未存入缓冲区
                    return False
        return False

    def encode(self, data: bytes):
        """
        将数据中的转义符替换为转义符+转义符

        然后计算转义后的长度, 将长度写入包头后返回

        如果原始数据长度大于 3072, 则进行分包
        :param data: 数据流
        :return: ([原始大小], [转义后大小], [封包后数据流])
        """
        npData = np.array(list(data))
        remainData = None
        if npData.shape[0] > 3072:
            remainData = npData[3072:]
            npData = npData[:3072]

        packageRawSize = npData.shape[0]
        escapeChar = DataPacket.escapeChar[0]
        # Start add escapeChar
        indexEscapeChars = np.argwhere(npData == escapeChar)
        # initNewData
        escapedData = npData.copy()
        count = 0
        for index in indexEscapeChars:
            escapedData = np.insert(escapedData, index[0] + count, escapeChar)
            count += 1
        # End add escapeChar
        packageSizeEscaped = escapedData.shape[0]
        # Add head
        encodedData = np.zeros(packageSizeEscaped + 5, dtype=np.uint32)
        encodedData[0] = escapeChar
        encodedData[1: 5] = list(str(packageSizeEscaped).zfill(4).encode("ascii"))
        encodedData[5:] = escapedData
        # This operation just can for 1D NDArray
        result = ([packageRawSize], [packageSizeEscaped], [bytes(list(encodedData))])

        if remainData is not None:
            remainResults = self.encode(bytes(remainData.tolist()))
            result[0].extend(remainResults[0])
            result[1].extend(remainResults[1])
            result[2].extend(remainResults[2])

        return result
