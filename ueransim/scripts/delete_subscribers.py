from pymongo import MongoClient

def delete_imsi_range(start_index, end_index, base_imsi_str, mongo_uri="mongodb://localhost:27017"):
    client = MongoClient(mongo_uri)
    db = client["open5gs"]

    base_number = int(base_imsi_str)

    for i in range(start_index, end_index + 1):
        imsi = f"{base_number + (i - start_index):015d}"
        result = db.subscribers.delete_one({"imsi": imsi})
        if result.deleted_count > 0:
            print(f"✅ Deleted IMSI {imsi}")
        else:
            print(f"⚠️ IMSI {imsi} not found")

    client.close()

# Example usage
if __name__ == "__main__":
    delete_imsi_range(start_index=1, end_index=10, base_imsi_str="001010000000010")
