function print_stats(depId) {
	print("Health Scores: " + db.hscore.find({deploymentId: ObjectId(depId)}).count())
	print("Covid 19 Risk Scores: " + db.covid19riskscore.find({deploymentId: ObjectId(depId)}).count())
	print("Daily Check-ins: " + db.covid19dailycheckin.find({deploymentId: ObjectId(depId)}).count())
}


function print_qa_stats() {
	print("--- Deployment ---")
	print_stats("5f31afdd17090187f1ffa1e8")
	print("\n")
}

function print_hs_eu_stats() {
	print("--- Chelsea ---")
	print_stats("5f3dcd5e5cc99c131a59b88c")
	print("\n")

	print("--- LetterOne ---")
	print_stats("5f4450f13432007b18200680")
	print("\n")
}

print_hs_eu_stats()