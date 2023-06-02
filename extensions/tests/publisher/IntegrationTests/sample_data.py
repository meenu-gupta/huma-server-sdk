sample_webhook_url = "https://webhook.site/64a6d6f5-34f3-450c-9497-63ffd468a9e9"
sample_expected_webhook_event_json = '{"primitives": [{"id": null, "userId": "43246ea1fc5b69c254abce67145047f1f285a619ab41ee84e542748ae911b272", "moduleId": "BloodPressure", "moduleConfigId": "617a6ae12ad9606b933e3db7", "moduleResultId": null, "deploymentId": "617a6ade2ad9606b933e3d8e", "version": 0, "deviceName": "iOS", "deviceDetails": null, "isAggregated": false, "aggregationPrecision": null, "startDateTime": "2021-11-24T10:09:17.694000Z", "endDateTime": null, "createDateTime": "2021-11-24T10:09:17.845000Z", "submitterId": "43246ea1fc5b69c254abce67145047f1f285a619ab41ee84e542748ae911b272", "correlationStartDateTime": null, "tags": null, "tagsAuthorId": null, "client": null, "server": {"hostUrl": "vb-ppserver.ngrok.io", "server": "1.17.0", "api": "V1"}, "ragThreshold": null, "flags": null, "diastolicValue": 80, "systolicValue": 92, "unitSi": null, "diastolicValueUnit": "mmHg", "systolicValueUnit": "mmHg", "_cls": "BloodPressure", "user": {"id": "43246ea1fc5b69c254abce67145047f1f285a619ab41ee84e542748ae911b272", "updateDateTime": "2021-11-11T19:03:16.148000Z", "createDateTime": "2021-10-06T14:38:21.150000Z", "lastSubmitDateTime": null, "givenName": null, "familyName": null, "gender": "MALE", "biologicalSex": "MALE", "ethnicity": null, "dateOfBirth": "1988-04-04", "email": null, "phoneNumber": null, "primaryAddress": null, "race": null, "bloodGroup": null, "emergencyPhoneNumber": null, "height": null, "additionalContactDetails": null, "familyMedicalHistory": null, "pastHistory": null, "presentSymptoms": null, "operationHistory": null, "chronicIllness": null, "allergyHistory": null, "pregnancy": null, "dateOfLastPhysicalExam": null, "extraCustomFields": null, "surgeryDetails": null, "fenlandCohortId": null, "nhsId": null, "insuranceNumber": null, "wechatId": null, "kardiaId": null, "pamThirdPartyIdentifier": null, "timezone": "UTC", "labels": null, "surgeryDateTime": null, "carePlanGroupId": null, "preferredUnits": null, "addressComponent": null, "onfidoApplicantId": null, "verificationStatus": null, "personalDocuments": null, "enrollmentId": 354, "enrollmentNumber": null, "deployments": null, "boardingStatus": null, "language": "en", "finishedOnboarding": true, "stats": {"taskCompliance": {"current": 0, "total": 14, "due": 0, "updateDateTime": "2021-11-11T19:03:16.121000Z", "percentage": 0}}, "ragScore": null, "flags": null, "unseenFlags": null, "recentFlags": null, "lastLoginDateTime": null, "badges": null, "consent": null, "econsent": null}}], "module_id": "BloodPressure", "deployment_id": "61926cbe9cb844829c967f8a", "device_name": "iOS", "module_config_id": "617a6ae12ad9606b933e3db7"}'
sample_expected_webhook_header = {"Content-Type": "application/json; charset=UTF-8"}
sample_event_dict = {
    "userId": "615db4dd92a28f0cee2e14c1",
    "moduleId": "BloodPressure",
    "moduleConfigId": "617a6ae12ad9606b933e3db7",
    "deploymentId": "61926cbe9cb844829c967f8a",
    "deviceName": "iOS",
    "startDateTime": "2021-11-09T14:28:37.630000Z",
    "primitives": [
        {
            "id": "618a8595a57e07e2de456e33",
            "userId": "615db4dd92a28f0cee2e14c1",
            "moduleId": "BloodPressure",
            "moduleResultId": "31f79109948c469bba0b3e202960d961",
            "moduleConfigId": "617a6ae12ad9606b933e3db7",
            "deploymentId": "61926cbe9cb844829c967f8a",
            "version": 0,
            "deviceName": "iOS",
            "deviceDetails": None,
            "isAggregated": False,
            "aggregationPrecision": None,
            "startDateTime": "2021-11-09T14:28:37.630000Z",
            "endDateTime": None,
            "createDateTime": "2021-11-09T14:28:37.767489Z",
            "submitterId": "615db4dd92a28f0cee2e14c1",
            "correlationStartDateTime": None,
            "tags": None,
            "tagsAuthorId": None,
            "client": None,
            "server": {
                "hostUrl": "vb-ppserver.ngrok.io",
                "server": "1.16.0",
                "api": "V1",
            },
            "ragThreshold": None,
            "flags": None,
            "diastolicValue": 80,
            "systolicValue": 92,
            "unitSi": None,
            "diastolicValueUnit": "mmHg",
            "systolicValueUnit": "mmHg",
            "_cls": "BloodPressure",
        }
    ],
}
