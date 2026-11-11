# lz78.py

def compress_data(data: bytes) -> bytes:
    """LZ78 壓縮二進位資料"""
    if not data:
        return b""

    # 初始化字典，索引 0 代表空位元組
    dictionary = {b"": 0}
    dict_size = 1
    
    out = bytearray()
    w = b""
    
    for b in data:
        wb = w + bytes([b])
        if wb in dictionary:
            w = wb
        else:
            # 輸出格式：(字典索引, 下一個字元)
            # 將字典索引轉為 2 bytes，並接上 1 byte 的字元
            out.extend(dictionary[w].to_bytes(2, 'big'))
            out.append(b)
            
            # 加入新字串到字典
            dictionary[wb] = dict_size
            dict_size += 1
            w = b""
            
            # 若字典滿了 (2 bytes 的上限是 65535)，則重置字典
            if dict_size == 65535:
                dictionary = {b"": 0}
                dict_size = 1

    # 如果檔案結束時，仍有尚未輸出的緩衝區內容，則只輸出索引 (2 bytes)
    if w:
        out.extend(dictionary[w].to_bytes(2, 'big'))
        
    return bytes(out)

def decompress_data(data: bytes) -> bytes:
    """LZ78 解壓縮二進位資料"""
    if not data:
        return b""

    dictionary = {0: b""}
    dict_size = 1
    
    out = bytearray()
    i = 0
    length = len(data)
    
    while i < length:
        # 讀取 2 bytes 的索引
        if i + 2 <= length:
            idx = int.from_bytes(data[i:i+2], 'big')
            i += 2
        else:
            break  # 檔案毀損或不完整
            
        # 讀取 1 byte 的字元
        if i < length:
            char_byte = data[i]
            i += 1
            
            # 重建字串
            entry = dictionary[idx] + bytes([char_byte])
            out.extend(entry)
            
            # 加入字典
            dictionary[dict_size] = entry
            dict_size += 1
            
            # 對應壓縮時的字典重置機制
            if dict_size == 65535:
                dictionary = {0: b""}
                dict_size = 1
        else:
            # 只剩下索引 (檔案結尾的特殊情況)
            out.extend(dictionary[idx])
            
    return bytes(out)
    
