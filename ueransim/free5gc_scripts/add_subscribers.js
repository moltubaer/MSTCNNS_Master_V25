for (let i = 1; i <= 1000; i++) {
    let imsi = String(100100000000001 + i - 1).padStart(15, "0");
    db.subscriber.insertOne({
      imsi: imsi,
      ueId: imsi,
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
            dnnInfos: [{ dnn: "internet" }]
          },
          "01112233": {
            dnnInfos: [{ dnn: "internet" }]
          }
        }
      },
      sessionManagementSubscriptionData: {
        singleNssai: { sst: 1, sd: "010203" },
        dnnConfigurations: {
          internet: {
            pduSessionTypes: {
              defaultSessionType: "IPV4",
              allowedSessionTypes: ["IPV4"]
            },
            sscModes: {
              defaultSscMode: 1,
              allowedSscModes: [1, 2, 3]
            },
            ambr: {
              uplink: "1 Gbps",
              downlink: "1 Gbps"
            },
            qosProfile: {
              "5qi": 9,
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
  }
  