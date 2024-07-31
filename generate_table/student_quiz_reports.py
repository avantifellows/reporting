def generate_student_quiz_reports(ddb):
    """
    Adds student quiz report table (v1)
    """
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


def generate_student_quiz_reports_v2(ddb):
    """
    Adds student quiz report table (v1)
    """
    ddb.create_table(
        TableName="student_quiz_reports_v2",
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "session_id", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "session_id", "KeyType": "HASH"},
            {"AttributeName": "user_id", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    print("Successfully created Student Quiz Reports V2 Table")


def add_secondary_index(ddb):
    table = ddb.Table("student_quiz_reports")
    response = table.update(
        AttributeDefinitions=[
            {"AttributeName": "session_id", "AttributeType": "S"},
            {"AttributeName": "user_id-section", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexUpdates=[
            {
                "Create": {
                    "IndexName": "gsi_user_id",
                    "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            }
        ],
    )
    print(response)


def drop_secondary_index(ddb, index_name):
    table = ddb.Table("student_quiz_reports")
    response = table.update(
        GlobalSecondaryIndexUpdates=[{"Delete": {"IndexName": index_name}}]
    )
    print(response)


def drop_student_quiz_reports(ddb):
    table = ddb.Table("student_quiz_reports")
    table.delete()
