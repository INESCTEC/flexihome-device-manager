?event rdf:type ke-devices:DeviceAccessChange .
?event saref:hasTimestamp ?timestamp .
?event ke-devices:newAccessStatus ?status .
?event ke-devices:hasConsumer ?kb .
?event ke-devices:hasResource ?device .
?device ic-device:hasDeviceID ?deviceId .
?device ke-devices:isRepresentedBy ?deviceSsa .