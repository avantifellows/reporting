def generate_student_quiz_reports(ddb):
    ddb.create_table(
        TableName="student_quiz_reports",
        AttributeDefinitions=[
            {"AttributeName": "session_id", "AttributeType": "S"},
            {"AttributeName": "user_id-section", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "session_id", "KeyType": "HASH"},
            {"AttributeName": "user_id-section", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    print("Successfully created Student Quiz Reports Table")


def drop_student_quiz_reports(ddb):
    table = ddb.Table("student_quiz_reports")
    table.delete()
