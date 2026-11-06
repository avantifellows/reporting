from unittest.mock import MagicMock

from db.bq_db import BigQueryDB

INJECTION = "x' OR '1'='1"


def _db_with_rows(rows):
    client = MagicMock()
    client.query.return_value.result.return_value = rows
    return BigQueryDB(client), client


def test_query_is_parameterized_not_interpolated():
    db, client = _db_with_rows([])
    db.get_student_qualification_data(INJECTION, "test-1")

    sql = client.query.call_args[0][0]
    assert "@user_id" in sql and "@test_id" in sql
    assert INJECTION not in sql
    assert "test-1" not in sql


def test_values_are_passed_as_query_parameters():
    db, client = _db_with_rows([])
    db.get_student_qualification_data(INJECTION, "test-1")

    params = {
        p.name: p.value
        for p in client.query.call_args.kwargs["job_config"].query_parameters
    }
    assert params == {"user_id": INJECTION, "test_id": "test-1"}


def test_numeric_ids_are_sent_as_strings():
    db, client = _db_with_rows([])
    db.get_student_qualification_data(1403899102, 42)

    params = {
        p.name: p.value
        for p in client.query.call_args.kwargs["job_config"].query_parameters
    }
    assert params == {"user_id": "1403899102", "test_id": "42"}


def test_returns_row_values():
    row = {
        "qualification_status": "Not Qualified",
        "marks_to_qualify": 120,
        "chapter_curriculum": "Kinematics",
        "dpp_recommendation": "https://example.com/dpp",
    }
    db, _ = _db_with_rows([row])
    assert db.get_student_qualification_data("u", "t") == row


def test_failure_falls_back_to_default():
    client = MagicMock()
    client.query.side_effect = RuntimeError("bq down")
    result = BigQueryDB(client).get_student_qualification_data("u", "t")
    assert result["qualification_status"] == "Qualified"
