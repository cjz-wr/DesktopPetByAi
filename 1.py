from cryptography.fernet import Fernet
import base64

# 尝试将提取的base64字符串解码为原始字节
raw_key = base64.b64decode(b'FmNHeapGTDaQxqHblLXK1MQSv2FTnsv3aIiFawlv3RcU=')
print(f"原始密钥长度: {len(raw_key)} 字节")

# 将原始密钥重新编码为URL安全的base64
urlsafe_key = base64.urlsafe_b64encode(raw_key)

token = b'gAAAAABpWx03biEtaj0qDFciRzYBs4lAnmp62SeYZkedwgCZ-DA09aqgJK2fMwnxE4ZUJCqT8P7Ss4172PR0SuxmcTSFtCy-hg=='
cipher = Fernet(urlsafe_key)
decrypted_data = cipher.decrypt(token)
print("解密内容:", decrypted_data.decode())