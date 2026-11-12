NYT_SYMBOL = -1 # NYT 節點
INTERNAL_SYMBOL = -2 # 內部節點

class Node:
    """
    節點類別
    """
    # 取代字典存屬性 (不然節點太多很吃記憶體)
    __slots__ = ['weight', 'parent', 'left', 'right', 'symbol']
    
    def __init__(self, weight=0, parent=0, left=0, right=0, symbol=0):
        """
        初始化

        Args:
            weight (int): 權重
            parent (int): 父節點的索引
            left (int): 左子節點的索引
            right (int): 右子節點的索引
            symbol (int): 代表字元的 ASCII (NYT 節點用 -1, 內部節點用 -2 區分)
        """
        self.weight = weight
        self.parent = parent
        self.left = left
        self.right = right
        self.symbol = symbol


class AdaptiveHuffman:
    """
    動態霍夫曼樹類別
    """
    def __init__(self):
        """
        初始化 (用 list 實作樹狀結構)
        """
        # 樹, 最多會有 256 個字元, 1 個 NYT, 256 個內部節點
        # 保留 nodes[0] 當作 None
        self.nodes = [Node() for _ in range(514)]

        # 初始 NYT
        self.nyt_index = 513
        self.nodes[self.nyt_index].symbol = NYT_SYMBOL 

        # 固定根節點
        self.root_index = 513

        # 儲存每個字元對應的節點索引的表
        self.map = [0] * 256

    def swap_nodes(self, a: int, b: int):
        """
        交換以 a, b 節點為 root 的子樹

        Args:
            a (int): a 節點在 nodes 中的索引
            b (int): b 節點在 nodes 中的索引
        """
        # 交換 a, b 各自指向的父節點
        self.nodes[a].parent, self.nodes[b].parent = self.nodes[b].parent, self.nodes[a].parent
        
        # 交換 a, b 節點在 nodes 中的位置
        self.nodes[a], self.nodes[b] = self.nodes[b], self.nodes[a]
        
        # 更新 a, b 節點的左右子節點的父節點索引
        if self.nodes[a].left != 0: self.nodes[self.nodes[a].left].parent = a
        if self.nodes[a].right != 0: self.nodes[self.nodes[a].right].parent = a
        if self.nodes[b].left != 0: self.nodes[self.nodes[b].left].parent = b
        if self.nodes[b].right != 0: self.nodes[self.nodes[b].right].parent = b
        
        # 更新字元對應表
        if self.nodes[a].symbol >= 0: self.map[self.nodes[a].symbol] = a
        if self.nodes[b].symbol >= 0: self.map[self.nodes[b].symbol] = b

    def update(self, node: int):
        """
        讀取字元後更新權重
        
        Args:
            node (int): 要更新權重 (+1) 的節點索引
        """
        while node != 0:
            max_idx = node
            
            # 找出 +1 前相同權重中離 root 最近的節點 (索引最大的)
            for i in range(node + 1, 514):
                if self.nodes[i].weight == self.nodes[node].weight:
                    max_idx = i
                elif self.nodes[i].weight > self.nodes[node].weight:
                    break
            
            # 如果離 root 最近的不是自己就交換
            if max_idx != node and max_idx != self.nodes[node].parent:
                self.swap_nodes(node, max_idx)
                node = max_idx
                
            self.nodes[node].weight = self.nodes[node].weight + 1
            node = self.nodes[node].parent # 往上的父節點繼續更新權重

    def add_symbol(self, symbol: int):
        """
        加入新字元 (第一次看到的)

        Args:
            symbol (int): 新字元的 ASCII
        """
        # 設定新的 NYT
        self.nodes[self.nyt_index - 2].symbol = NYT_SYMBOL
        self.nodes[self.nyt_index - 2].parent = self.nyt_index
        
        # 設定新的字元葉節點
        self.nodes[self.nyt_index - 1].symbol = symbol
        self.nodes[self.nyt_index - 1].parent = self.nyt_index
        
        # 將舊的 NYT 變成內部節點
        self.nodes[self.nyt_index].symbol = INTERNAL_SYMBOL
        self.nodes[self.nyt_index].left = self.nyt_index - 2
        self.nodes[self.nyt_index].right = self.nyt_index - 1

        # 更新查表陣列
        self.map[symbol] = self.nyt_index - 1

        # 更新 NYT 的索引
        self.nyt_index = self.nyt_index - 2
        
        # 從新的字元葉節點開始向上更新權重
        self.update(self.nyt_index + 1)

    def get_path(self, node: int) -> list:
        """
        取得某節點當下的霍夫曼編碼

        Args:
            node (int): 要取得編碼的節點索引
        
        Returns:
            list: 該節點字元的編碼
        """
        path = []
        while self.nodes[node].parent != 0:
            # 該節點是父節點的左子節點
            if self.nodes[self.nodes[node].parent].left == node:
                path.append(0)
            # 該節點是父節點的右子節點
            else:
                path.append(1)
            
            node = self.nodes[node].parent

        path.reverse()  # 反轉 (因為是由下往上)
        return path


class BitWriter:
    """
    位元組轉換類別
    """
    def __init__(self):
        """
        初始化
        """
        self.buffer = bytearray() # 存放打包好的位元組們
        self.current_byte = 0 # 打包用位元組 (預設為 00000000)
        self.bit_count = 0 # 下一個位元要放的位置 (由高放到低)

    def write_bit(self, bit: int):
        """
        寫入一個位元

        Args:
            bit (int): 要寫入的位元的值 (0 或 1)
        """
        if bit != 0:
            self.current_byte = self.current_byte | (1 << (7 - self.bit_count))

        self.bit_count = self.bit_count + 1

        # 集滿 8 個位元
        if self.bit_count == 8:
            self.buffer.append(self.current_byte)
            self.current_byte = 0
            self.bit_count = 0

    def write_path(self, path: list):
        """
        寫入一串位元

        Args:
            path (list): 要寫入的位元 list
        """
        for bit in path:
            self.write_bit(bit)

    def write_bits(self, value: int, count: int):
        """
        寫入指定長度的整數 (例如: 新字元的 ASCII, 8 bits)
        """
        # 將整數拆成位元後從高位元開始逐個位元取出並寫入
        for i in range(count):
            bit = (value >> (count - 1 - i)) & 1
            self.write_bit(bit)

    def flush(self) -> bytearray:
        """
        輸出結果 (self.buffer 的內容)

        Returns:
            bytearray: 打包好的一串位元組
        """
        # 不足 8 位元的也直接送出 (後面都會是 0)
        if self.bit_count > 0:
            self.buffer.append(self.current_byte)

        return self.buffer


class BitReader:
    """
    位元轉換類別
    """
    def __init__(self, data: bytes):
        """
        初始化

        Args:
            data (bytes): 要拆成位元的一串位元組
        """
        self.data = data # 一串位元組
        self.byte_index = 0 # 讀到第幾個位元組
        self.bit_index = 0 # 讀到位元組的第幾個位元

    def read_bit(self) -> int:
        """
        讀取一個位元

        Returns:
            int: 讀出的位元
        """
        if self.byte_index >= len(self.data):
            raise EOFError("Unexpected end of bit stream")
        
        bit = (self.data[self.byte_index] >> (7 - self.bit_index)) & 1

        self.bit_index = self.bit_index + 1

        if self.bit_index == 8:
            self.bit_index = 0
            self.byte_index = self.byte_index + 1

        return bit

    def read_bits(self, count: int) -> int:
        """
        讀取指定長度的位元 (例如: 新字元的 ASCII, 8 bits)

        Args:
            count (int): 要讀取的位元數

        Returns:
            int: 讀取的位元序列之整數值
        """
        value = 0
        for _ in range(count):
            value = (value << 1) | self.read_bit()
        return value


def core_compress(input_data: bytes) -> bytearray:
    """
    壓縮

    Args:
        input_data (bytes): 要壓縮的位元組序列

    Returns:
        bytearray: 壓縮後的位元組序列
    """
    writer = BitWriter()
    tree = AdaptiveHuffman()

    for byte in input_data:
        if tree.map[byte] != 0:
            # 字元已存在, 輸出該字元路徑並更新樹
            path = tree.get_path(tree.map[byte])
            writer.write_path(path)
            tree.update(tree.map[byte])
        else:
            # 新字元, 輸出 NYT 路徑 -> 原字元 -> 加進樹
            path = tree.get_path(tree.nyt_index)
            writer.write_path(path)
            writer.write_bits(byte, 8)
            tree.add_symbol(byte)
            
    return writer.flush() # 回傳壓縮後結果


def core_decompress(input_data: bytes, original_len: int) -> bytearray:
    """
    解壓縮

    Args:
        input_data (bytes): 要解壓縮的位元組序列
        original_len (int): 有效的字元數

    Returns:
        bytearray: 解壓縮後的位元組序列
    """
    reader = BitReader(input_data)
    output = bytearray()

    if original_len == 0:
        return output

    tree = AdaptiveHuffman()

    # 處理第一個字元
    first_byte = reader.read_bits(8)
    output.append(first_byte)
    tree.add_symbol(first_byte)

    while len(output) < original_len:
        curr = tree.root_index
        
        # 從 root 往下走訪樹直到抵達葉節點
        while tree.nodes[curr].left != 0 and tree.nodes[curr].right != 0:
            bit = reader.read_bit()
            if bit == 0:
                curr = tree.nodes[curr].left
            else:
                curr = tree.nodes[curr].right

        if tree.nodes[curr].symbol == NYT_SYMBOL:
            # 抵達 NYT 節點, 讀取接下來的字元輸出並新增進樹
            new_byte = reader.read_bits(8)
            output.append(new_byte)
            tree.add_symbol(new_byte)
        else:
            # 抵達已知字元節點, 直接輸出並更新樹
            sym = tree.nodes[curr].symbol
            output.append(sym)
            tree.update(curr)

    return output


def compress_data(input_data: bytes) -> bytes:
    """
    給 JS 呼叫: 壓縮並封裝 5 bytes 的檔頭
    
    Args:
        input_data (bytes): 要壓縮的位元組序列
    
    Returns:
        bytes: 壓縮並加上檔頭的位元組序列
    """
    # 空資料處理
    if not input_data:
        return bytes([0x00])

    compressed_body = core_compress(input_data) # 壓縮
    orig_len = len(input_data) # 原始資料長度
    
    result = bytearray()
    
    # 判斷壓縮後是否反而變大
    if len(compressed_body) >= len(input_data):
        result.append(0x00) # 0x00 代表無壓縮
        result.extend(orig_len.to_bytes(4, byteorder='little'))
        result.extend(input_data)
    else:
        result.append(0x01) # 0x01 代表已壓縮
        result.extend(orig_len.to_bytes(4, byteorder='little'))
        result.extend(compressed_body)
        
    return bytes(result)


def decompress_data(input_data: bytes) -> bytes:
    """
    給 JS 呼叫: 解析檔頭並解壓縮

    Args:
        input_data (bytes): 要解壓縮的位元組序列
    
    Returns:
        bytes: 解壓縮後的位元組序列   
    """
    # 不符合格式的資料處理 (連檔頭都沒有)
    if len(input_data) < 5:
        return bytes()

    # 解析檔頭
    flag = input_data[0]
    orig_len = int.from_bytes(input_data[1:5], byteorder='little')
    payload = input_data[5:]

    # 未壓縮資料處理
    if flag == 0x00:
        return payload[:min(orig_len, len(payload))]

    # 解壓縮
    try:
        return bytes(core_decompress(payload, orig_len))
    except EOFError:
        return payload  # 解碼失敗時退回原始 payload