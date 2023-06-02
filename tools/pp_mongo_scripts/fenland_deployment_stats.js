batchSize = 4000
DBQuery.shellBatchSize = batchSize;

deploymentId = "5f273e030319b4ad57b7a305" // PROD
//deploymentId = "5f0d6488882b387e2359e606" // QA



function getKey(o, key) {
    if (key in o) {
        return o[key]
    }
    return ''
}

function formattedDate(d) {
    var year = d.getFullYear();

    var month = (1 + d.getMonth()).toString();
    month = month.length > 1 ? month : '0' + month;

    var day = d.getDate().toString();
    day = day.length > 1 ? day : '0' + day;

    return year + "-" + month + "-" + day;
}


function get_users(deploymentId) {
    return db.user.find({
        "roles.resource": "deployment/" + (deploymentId)
    })
}

function get_users_with_fenland_id(deploymentId) {
    return db.user.find({
        "$and": [{"roles.resource": "deployment/" + (deploymentId)}, {"fenlandCohortId" : { "$ne" : null }}]
    }).batchSize(batchSize)
}

function get_users_without_fenland_id(deploymentId) {
    return db.user.find({
        "$and": [{"roles.resource": "deployment/" + (deploymentId)}, {"fenlandCohortId" : { "$eq" : null }}]
    }).batchSize(batchSize)
}


function print_user(u) {
	print(String(u["fenlandCohortId"]) + "," + u["createDateTime"].toISOString())
}

function print_user_details(u) {
    dobStr = ''
    dobKey = getKey(u, 'dateOfBirth')
    if (dobKey !== '') {
        dobStr = formattedDate(dobKey)
    }
    print(u["_id"].str + "," +
            getKey(u, "email") + "," +
            '"' + getKey(u, "phoneNumber") + '"' + "," +
            getKey(u, "givenName") + "," +
            getKey(u, "familyName") + "," +
            dobStr + "," +
            u["createDateTime"].toISOString()
        )
}


function print_fenland_users_csv(deploymentId) {
    print("cohort id,sign up timestamp")
    users = get_users_with_fenland_id(deploymentId)
    while (users.hasNext()) {
        print_user(users.next())
    }
}

function print_fenland_users_without_cohort_csv(deploymentId) {
    print("huma id,email,phone number,given name,family name,dob,sign up timestamp")
    users = get_users_without_fenland_id(deploymentId)
    while (users.hasNext()) {
        print_user_details(users.next())
    }
}

function print_fenland_users_stats(deploymentId) {
    total = get_users(deploymentId).count()
    total_with_fenland_id = get_users_with_fenland_id(deploymentId).count()

    print( " ------- Deployment [" + deploymentId + "] -------")
    print("Total: " + total)
    print("Total with fenland id: " + total_with_fenland_id)
    print("Total without fenland id: " + (total - total_with_fenland_id))
}



if (mode === 'printuserwithcohortidcsv') {
    print_fenland_users_csv(deploymentId)
} else if (mode === 'printuserwithoutcohortidcsv') {
    print_fenland_users_without_cohort_csv(deploymentId)
} else if (mode === 'printstats') {
    print_fenland_users_stats(deploymentId)
}