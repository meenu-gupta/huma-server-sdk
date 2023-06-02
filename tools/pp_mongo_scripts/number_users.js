function print_stats(depId) {
	print("# of users: " + db.user.find({"roles.resource": "deployment/"+depId}).count())
}


function print_qa_stats() {
	print("--- Deployments ---")
	deps = db.deployment.find({})
	while (deps.hasNext()) {
	    d = deps.next()
		print("+ Deployment [" + d["name"] + "]")
      	print_stats(d["_id"].str)
		print("\n")
	}
}

print_qa_stats()