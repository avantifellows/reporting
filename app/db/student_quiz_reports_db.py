from botocore.exceptions import ClientError
from boto3.resources.base import ServiceResource

class StudentQuizReportsDB:
    def __init__(self, db: ServiceResource) -> None:
        self.__db = db

    def get_all(self):
        table = self.__db.Table('student_quiz_reports')
        response = table.scan()
        return response.get('Items', [])

    def get_student_quiz_report(self, uid: str):
        try:
            table = self.__db.Table('student_quiz_reports')
            response = table.get_item(Key={'uid': uid})
            return response['Item']
        except ClientError as e:
            raise ValueError(e.response['Error']['Message'])

    def create_student_quiz_report(self, student_quiz_report: dict):
        table = self.__db.Table('student_quiz_reports')
        response = table.put_item(Item=student_quiz_report)
        return response

    def update_student_quiz_report(self, student_quiz_report: dict):
        table = self.__db.Table('student_quiz_reports')
        response = table.update_item(
            Key={'uid': student_quiz_report.get('uid')},
            UpdateExpression="""
                set
                    quiz_id=:quiz_id,
                    quiz_name=:quiz_name,
                    quiz_stats=:quiz_stats,
                    score_details=:score_details
            """,
            ExpressionAttributeValues={
                ':quiz_id': student_quiz_report.get('quiz_id'),
                ':quiz_name': student_quiz_report.get('quiz_name'),
                ':quiz_stats': student_quiz_report.get('quiz_stats'),
                ':score_details': student_quiz_report.get('score_details')
            },
            ReturnValues="UPDATED_NEW"
        )
        return response

    def delete_student_quiz_report(self, uid: str):
        table = self.__db.Table('student_quiz_reports')
        response = table.delete_item(
            Key={'uid': uid}
        )
        return response