from pymongo import MongoClient
from bson import ObjectId

def register_open5gs_ues(start_index, end_index, base_imsi, mongo_uri="mongodb://localhost:27017"):
    client = MongoClient(mongo_uri)
    db = client["open5gs"]

    for i in range(start_index, end_index + 1):
        imsi = f"{base_imsi + (i - start_index):015d}"

        subscriber = {
            "imsi": imsi,
            "imeisv": "4370816125816151",
            "security": {
                "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
                "amf": "8000",
                "opc": "E8ED289DEBA952E4283B54E88E6183CA",
                "sqn": 0
            },
            "slice": [
                {
                    "sst": 1,
                    "default_indicator": True,
                    "session": [
                        {
                            "name": "internet",
                            "type": 3,
                            "qos": {
                                "index": 9,
                                "arp": {
                                    "priority_level": 8,
                                    "pre_emption_capability": 1,
                                    "pre_emption_vulnerability": 1
                                }
                            },
                            "ambr": {
                                "uplink": {"value": 1, "unit": 3},
                                "downlink": {"value": 1, "unit": 3}
                            }
                        }
                    ]
                }
            ],
            "ambr": {
                "uplink": {"value": 1, "unit": 3},
                "downlink": {"value": 1, "unit": 3}
            },
            "access_restriction_data": 32,
            "subscriber_status": 0,
            "operator_determined_barring": 0,
            "network_access_mode": 0,
            "subscribed_rau_tau_timer": 12,
            "msisdn": [],
            "mme_host": [],
            "mme_realm": [],
            "purge_flag": [],
            "schema_version": 1,
            "__v": 0
        }

        db.subscribers.insert_one(subscriber)
        print(f"✅ Registered IMSI {imsi}")

    client.close()

# Example usage:
register_open5gs_ues(start_index=1, end_index=10, base_imsi=001010000000010)
