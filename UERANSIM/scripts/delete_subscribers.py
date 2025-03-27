from pymongo import MongoClient

def delete_imsi_range(start_index, end_index, base_imsi, mongo_uri="mongodb://localhost:27017"):
    client = MongoClient(mongo_uri)
    db = client["open5gs"]

    for i in range(start_index, end_index + 1):
        imsi = f"{base_imsi + (i - start_index):015d}"
        result = db.subscribers.delete_one({"imsi": imsi})
        if result.deleted_count > 0:
            print(f"✅ Deleted IMSI {imsi}")
        else:
            print(f"⚠️ IMSI {imsi} not found")

    client.close()

# Example usage
if __name__ == "__main__":
    # Deletes IMSIs from 001010000000010 to 001010000000020
    delete_imsi_range(start_index=1, end_index=10, base_imsi=001010000000010)
