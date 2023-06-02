function get_consent_user(userId) {
    return db.consentlog.findOne({
        "userId": ObjectId(userId)
    })
}

function get_blq(userId) {
    return db.questionnaire.findOne({
        "userId": ObjectId(userId)
    })
}

function print_details(userId) {
    print("+ User Id:" + userId)
    consent_log = get_consent_user(userId)
    if (consent_log) {
        print(" > has consent")
        blq = get_blq(userId)
        if (blq) {
            print(" > has questionnaire ( in short baseline questionnaire )")
        } else {
            print(" > has no questionnaire ( in short baseline questionnaire )")
        }
    } else {
        print(" > has no consent")
    }
}

all_missing_ids = [
    "5f8879122fc8f385aa427a29",
    "5f8d66ecbcb2537a8f6c5f47",
    "5f8d91ef2fc8f385aa428743",
    "5f8df9f977159e1e29994b62",
    "5f8f16a52fc8f385aa428ad3",
    "5f95ad33edb98c48feb56a9e",
    "5f96b3c10948c0ace9e28a3b",
    "5f97cd9c0948c0ace9e28cbe",
    "5f9aaa10b9488a55cc2f7865",
    "5fa2d5e60948c0ace9e2b3e0",
    "5faa9e9138b5f7504b06c7ab"
]

all_missing_ids.forEach(print_details)