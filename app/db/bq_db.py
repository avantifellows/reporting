from google.cloud import bigquery


class BigQueryDB:
    def __init__(self, client: bigquery.Client) -> None:
        self.__client = client

    def get_student_qualification_data(self, user_id, test_id):
        query_string = f"""
        SELECT
            qualification_status,
            marks_to_qualify,
            chapter_curriculum,
            dpp_recommendation
        FROM
            avantifellows.prod_af_db.student_profile_al
        WHERE
            user_id = '{user_id}'
            AND test_id = '{test_id}'
            AND section = 'overall'
        LIMIT 1
        """

        try:
            query_job = self.__client.query(query_string)
            results = list(query_job.result())

            if results:
                return {
                    "qualification_status": results[0]["qualification_status"],
                    "marks_to_qualify": results[0]["marks_to_qualify"],
                    "chapter_curriculum": results[0]["chapter_curriculum"],
                    "dpp_recommendation": results[0]["dpp_recommendation"],
                }
            else:
                # Default fallback data if no results
                return {
                    "qualification_status": "Qualified",
                    "marks_to_qualify": None,
                    "chapter_curriculum": "",
                    "dpp_recommendation": "",
                }
        except Exception as e:
            print(f"BigQuery error: {str(e)}")
            # Default fallback data in case of error
            return {
                "qualification_status": "Qualified",
                "marks_to_qualify": None,
                "chapter_curriculum": "",
                "dpp_recommendation": "",
            }
