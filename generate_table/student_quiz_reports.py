import boto3

def generate_student_quiz_reports(ddb):
    ddb.create_table(
        TableName='student_quiz_reports',
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'quiz_id',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'student_id',
                'AttributeType': 'S'
            }

        ],
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        GlobalSecondaryIndexes=[
        {
            'IndexName': 'quiz_id',
            'KeySchema': [
                {
                    'AttributeName': 'quiz_id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'student_id',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'ALL',
            }
            },
        ],
        BillingMode='PAY_PER_REQUEST',

        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    print('Successfully created Student Quiz Reports Table')

def drop_student_quiz_reports(ddb):
    table = ddb.Table('student_quiz_reports')
    table.delete()