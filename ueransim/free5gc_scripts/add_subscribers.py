from pymongo import MongoClient

def register_free5gc_ues(start_index, end_index, base_imsi_str, mongo_uri="mongodb://localhost:27017"):
    client = MongoClient(mongo_uri)
    db = client["free5gc"]
    collection = db["subscriber"]

    base_number = int(base_imsi_str)

    for i in range(start_index, end_index + 1):
        imsi = f"{base_number + (i - start_index):015d}"
        subscriber = {
            "imsi": imsi,
            "ueId": imsi,
            "servingPlmnId": "00101",
            "authSubscription": {
                "permanentKey": {
                    "permanentKey": "8baf473f2f8fd09487cccbd7097c6862"
                },
                "opc": {
                    "opcValue": "8e27b6af0e692e750f32667a3b14605d"
                },
                "authenticationMethod": "5G_AKA",
                "milenage": {
                    "amf": "8000"
                }
            },
            "amPolicyData": {
                "subscCats": ["free5gc"]
            },
            "smfSelectionData": {
                "subscribedSnssaiInfos": {
                    "01010203": {
                        "dnnInfos": [
                            {
                                "dnn": "internet"
                            }
                        ]
                    },
                    "01112233": {
                        "dnnInfos": [
                            {
                                "dnn": "internet"
                            }
                        ]
                    }
                }
            },
            "sessionManagementSubscriptionData": {
                "singleNssai": {
                    "sst": 1,
                    "sd": "010203"
                },
                "dnnConfigurations": {
                    "internet": {
                        "pduSessionTypes": {
                            "defaultSessionType": "IPV4",
                            "allowedSessionTypes": ["IPV4"]
                        },
                        "sscModes": {
                            "defaultSscMode": 1,
                            "allowedSscModes": [1, 2, 3]
                        },
                        "ambr": {
                            "uplink": "1 Gbps",
                            "downlink": "1 Gbps"
                        },
                        "qosProfile": {
                            "5qi": 9,
                            "arp": {
                                "priorityLevel": 8,
                                "preemptCap": "SHALL_NOT_TRIGGER_PREEMPTION",
                                "preemptVuln": "NOT_PREEMPTABLE"
                            }
                        }
                    }
                }
            }
        }

        collection.insert_one(subscriber)
        print(f"✅ Registered IMSI {imsi}")

    client.close()

# Example usage
register_free5gc_ues(start_index=1, end_index=10, base_imsi_str="001010000000001")
