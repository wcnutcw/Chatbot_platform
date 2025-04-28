from elasticsearch import Elasticsearch

# สมมติว่า server รันที่ localhost:9200
es = Elasticsearch("http://localhost:9200")

# เช็คเวอร์ชัน
info = es.info()
print(info['version']['number'])