def sample_user(phone_number: str = None):
    return {
        "method": 1,
        "phoneNumber": phone_number or "+380999999999",
        "email": "m@gmail.com",
        "displayName": "test",
        "validationData": {"activationCode": "53924415"},
        "userAttributes": {
            "familyName": "hey",
            "givenName": "test",
            "dob": "1988-02-20",
            "gender": "MALE",
        },
        "clientId": "ctest1",
        "projectId": "ptest1",
    }
