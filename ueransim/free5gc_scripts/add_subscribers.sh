#!/bin/bash

# MongoDB connection details
MONGO_HOST="localhost"  # Use "db" if you're running this from another container in the same Docker network
MONGO_PORT="27017"
DB_NAME="free5gc"
COLLECTION="subscriber"

# IMSI generation parameters
PREFIX="001010"
START_INDEX=1
END_INDEX=1000

echo "📡 Starting insert of ${END_INDEX} subscribers into MongoDB..."

for ((i=START_INDEX; i<=END_INDEX+1; i++)); do
  IMSI="${PREFIX}$(printf "%09d" $i)"

  cat <<EOF | mongo --host "$MONGO_HOST" --port "$MONGO_PORT" "$DB_NAME"
db.$COLLECTION.insertOne({
  imsi: "$IMSI",
  ueId: "$IMSI",
  servingPlmnId: "00101",
  authSubscription: {
    permanentKey: {
      permanentKey: "8baf473f2f8fd09487cccbd7097c6862"
    },
    opc: {
      opcValue: "8e27b6af0e692e750f32667a3b14605d"
    },
    authenticationMethod: "5G_AKA",
    milenage: {
      amf: "8000"
    }
  },
  amPolicyData: {
    subscCats: ["free5gc"]
  },
  smfSelectionData: {
    subscribedSnssaiInfos: {
      "01010203": {
        dnnInfos: [
          { dnn: "internet" }
        ]
      },
      "01112233": {
        dnnInfos: [
          { dnn: "internet" }
        ]
      }
    }
  },
  sessionManagementSubscriptionData: {
    singleNssai: {
      sst: "1",
      sd: "010203"
    },
    dnnConfigurations: {
      internet: {
        pduSessionTypes: {
          defaultSessionType: "IPV4",
          allowedSessionTypes: ["IPV4"]
        },
        sscModes: {
          defaultSscMode: "1",
          allowedSscModes: [1, 2, 3]
        },
        ambr: {
          uplink: "1 Gbps",
          downlink: "1 Gbps"
        },
        qosProfile: {
          "5qi": "9",
          arp: {
            priorityLevel: 8,
            preemptCap: "SHALL_NOT_TRIGGER_PREEMPTION",
            preemptVuln: "NOT_PREEMPTABLE"
          }
        }
      }
    }
  }
});
EOF

  echo "✅ Inserted $IMSI"
done

echo "🎉 All done! Total inserted: $((END_INDEX - START_INDEX + 1))"
