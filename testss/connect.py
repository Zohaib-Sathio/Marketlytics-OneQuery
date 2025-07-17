from pinecone import Pinecone

pc = Pinecone(api_key="pcsk_5AiPYH_TP21LoJgcYyN1xBvCnLY1v3tY2VTNenKDapDcsQwFhrwemTdD9iUqwZbePyKxaA")
index = pc.Index("marketlytics-onequery")
print(index)