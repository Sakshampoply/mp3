import certifi
from pymongo import MongoClient

uri = "mongodb+srv://saksham:11008712@mini-project-3.wdhjfva.mongodb.net/?retryWrites=true&w=majority&appName=mini-project-3"
client = MongoClient(uri, tls=True, tlsCAFile=certifi.where())
print(client.server_info())
