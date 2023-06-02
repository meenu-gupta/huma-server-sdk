function get_consent_by_deployment_id(deploymentId) {
    return db.deployment.findOne({
        _id: ObjectId(deploymentId)
    })["consent"]
}
function print_consent_stats(consentId, consentRevision) {
    total = db.consentlog.find({
        'consentId': consentId,
        'revision': consentRevision
    }).count()
		option_0 = db.consentlog.find({
        'consentId': consentId,
        'revision': consentRevision,
				'sharingOption': 0
    }).count()
		option_1 = db.consentlog.find({
        'consentId': consentId,
        'revision': consentRevision,
				'sharingOption': 1
    }).count()
		print("Total: " + total)
		print("\nTotal third-party sharing: " + option_0)
		print("\nTotal not third-party sharing: " + option_1)
}

deploymentId = "5f273e030319b4ad57b7a305" // PROD
deploymentId = "5f0d6488882b387e2359e606" // QA
consent = get_consent_by_deployment_id(deploymentId)
print( " ------- Deployment [" + deploymentId + "] -------\n")
print_consent_stats(consent["id"], consent["revision"])