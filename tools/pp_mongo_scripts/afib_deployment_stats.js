batchSize = 4000
DBQuery.shellBatchSize = batchSize;

deploymentId = "5f275248ab5e0704648b1aa4" // PROD
//deploymentId = "5f0d6488882b387e2359e606" // QA

function get_users(deploymentId) {
    return db.user.find({
        "roles.resource": "deployment/" + deploymentId, "roles.roleId": "User"
    })
}

function print_user(u) {
    print('"' + u["_id"].str + '","' + u["createDateTime"].toISOString() + '"')
}

function print_users_csv(deploymentId) {
    print("Patient ID,CreateDateTime")
    users = get_users(deploymentId)
    while (users.hasNext()) {
        print_user(users.next())
    }
}

if (mode === 'printuserscsv') {
    print_users_csv(deploymentId)
}