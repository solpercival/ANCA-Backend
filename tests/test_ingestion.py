from pathlib import Path

import pytest
import ingestion.indexers as indexers
from ingestion.chunker import chunk_markdown, RawChunk
from ingestion.pipeline import collect_markdown
from rag_engine.config import get_settings
import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
import httpx

def test_chunk_markdown_splits_on_headers_and_keeps_content():
    markdown = """# Intro
alpha

## Details
beta

```python
print('hello')
```

# Next
charlie
"""

    chunks = chunk_markdown(markdown, "sample.md")

    assert len(chunks) >= 2
    assert any("Intro" in chunk.text for chunk in chunks)
    assert any("Details" in chunk.text for chunk in chunks)
    assert any("print('hello')" in chunk.text for chunk in chunks)
    assert all(chunk.source == "sample.md" for chunk in chunks)

def test_chunk_markdown_splits_code():
    markdown = """
    ## Content
    ```python
    print("hello world!")

    sum = 0
    for i in range(5):
        sum += i
    ```

    Extra text content as text
    """
    chunks = chunk_markdown(markdown, "sample.md")

    assert len(chunks) >= 2
    assert (len(list(filter(lambda x: x.kind == "code", chunks))) == 1)
    assert any("code" == chunk.kind for chunk in chunks)
    assert any("text" == chunk.kind for chunk in chunks)
    assert any("for i in range(5)" in chunk.text for chunk in chunks)
    assert all("Content" in chunk.headers.values() for chunk in chunks)
    assert all(chunk.source == "sample.md" for chunk in chunks)


def test_chunk_markdown_splits_list():
    markdown="""
    ## Content

    ### List 1 (Numbered)
    1. Item A
    2. Item B
    3. Item C

    ### List 2 (Unordered List)
    * alpha
    * beta
        * beta-1
            * beta-1.1
            * beta-1.2
        * beta-2
        * beta-3
    * epsilon
    * zeta
    * gamma
    

    Extra text content as text  
    """
    chunks = chunk_markdown(markdown, "sample.md")
    
    assert len(chunks) >= 3
    assert (len(list(filter(lambda x: x.kind == "list", chunks))) == 2)
    assert any("list" == chunk.kind for chunk in chunks)
    assert any("text" == chunk.kind for chunk in chunks)
    assert any("beta-1" in chunk.text for chunk in chunks)
    assert all("Content" in chunk.headers.values() for chunk in chunks)
    assert any("List 1 (Numbered)" in chunk.headers.values() for chunk in chunks)
    assert all(chunk.source == "sample.md" for chunk in chunks)
    

def test_chunk_markdown_splits_table():
    markdown="""
    ## Content

    ### Table Sample
    | Task ID | Task Description | Priority | Status | Due Date |
    | --- | --- | --- | --- | --- |
    | T-101 | Database Schema Migration | High | In Progress | 2026-06-15 |
    | T-102 | User Authentication API | Critical | Completed | 2026-06-10 |
    | T-103 | Frontend Dashboard Redesign | Medium | Planning | 2026-06-30 |
    | T-104 | Automated Testing Suite | High | Not Started | 2026-07-05 |
    | T-105 | Performance Optimization | Low | On Hold | 2026-07-15 |

    Extra text content as text  
    """
    
    chunks = chunk_markdown(markdown, "sample.md")

    assert len(chunks) >= 2
    assert (len(list(filter(lambda x: x.kind == "table", chunks))) == 1)
    assert any("table" == chunk.kind for chunk in chunks)
    assert any("text" == chunk.kind for chunk in chunks)
    assert any("Task ID" in chunk.text for chunk in chunks)
    assert all("Content" in chunk.headers.values() for chunk in chunks)
    assert any("Table Sample" in chunk.headers.values() for chunk in chunks)
    assert all(chunk.source == "sample.md" for chunk in chunks)

def test_collect_markdown_reads_nested_markdown_files(tmp_path):
    docs = tmp_path / "docs"
    nested = docs / "nested"
    nested.mkdir(parents=True)

    (docs / "a.md").write_text("# A\nfirst\n", encoding="utf-8")
    (nested / "b.md").write_text("# B\nsecond\n", encoding="utf-8")

    chunks = collect_markdown(docs)

    assert len(chunks) == 2
    texts = {chunk.text for chunk in chunks}
    assert any("# A" in text for text in texts)
    assert any("# B" in text for text in texts)
@pytest.mark.integration
def test_sparse_embedding():
    chunks = [RawChunk(text="test script", source="", headers=[], kind="text"),
              RawChunk(text="motion", source="", headers=[], kind="text")]

    settings = get_settings()
    with httpx.Client(timeout=120.0) as client:
        sparse_vecs = indexers._sparse_embed(chunks=chunks, client=client)

    assert len(sparse_vecs) == len(chunks)
    assert all(sparse_vecs)                                   # non-empty embeddings
    assert all(len(vec) <= settings.lexical_dim for vec in sparse_vecs)


@pytest.mark.integration
def test_dense_embedding():
    chunks = [RawChunk(text="test script", source="", headers=[], kind="text"),
              RawChunk(text="motion", source="", headers=[], kind="text")]

    settings = get_settings()
    with httpx.Client(timeout=120.0) as client:
        dense_vecs = indexers._dense_embed(chunks=chunks, client=client)

    assert len(dense_vecs) == len(chunks)
    assert all(len(vec) == settings.semantic_dim for vec in dense_vecs)
    
def test_single_alarm_insert():
    settings = get_settings()
    sample_alarm = {
        "code": f"am{settings.alarm_delim}tc{settings.alarm_delim}001",
        "title": "Test Alarm Code Title",
        "domain": "TEST-CODE",
        "severity": 200,
        "severity_category": "Info",
        "alarm_text": "Further description of the alarm",
        "data_fields": {}
    }

    sample_data = {
        "_modules": {"tc": "TEST-CODE"},
        "alarms": [sample_alarm]
    }

    # populate db with 1 record
    indexers.populate_alarms(sample_data)

    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            module_test = cursor.execute("""
                SELECT * FROM alarm_module
                WHERE code = %s;
            """, [sample_alarm["code"].split(settings.alarm_delim)[1]],).fetchall()

            # verify 1 insertion made
            expected_module_code = sample_alarm["code"].split(settings.alarm_delim)[1]
            assert (len(module_test) >= 1)
            assert any((module["code"] == expected_module_code) and (module["title"] == sample_alarm["domain"]) for module in module_test)

            expected_sequence = sample_alarm["code"].split(settings.alarm_delim)[2]
            expected_origin = sample_alarm["code"].split(settings.alarm_delim)[0]
            code_test = cursor.execute("""
                SELECT * from alarm_code
                WHERE alarm_sequence = %s AND origin = %s AND module = %s;
            """, (expected_sequence, expected_origin, module_test[0]["id"]),).fetchall()

            assert (len(code_test) >= 1)
            assert any(entry["title"] == sample_alarm["title"] for entry in code_test)
            assert any(entry["severity_score"] == sample_alarm["severity"] for entry in code_test)
            assert any(entry["severity_category"] == sample_alarm["severity_category"].lower() for entry in code_test)
            assert any(entry["alarm_text"] == sample_alarm["alarm_text"] for entry in code_test)

def test_duplicate_alarm_insert():
    settings = get_settings()
    sample_alarm = {
        "code": f"am{settings.alarm_delim}tc{settings.alarm_delim}001", "title": "Test Alarm Code Title", "domain": "TEST-CODE",
        "severity": 200, "severity_category": "Info", "alarm_text": "Further description of the alarm", "data_fields": {}
    }

    # test whether code can handle multiple duplicate records insert
    # entries should be unique, error occurs when more than 1 result appears
    sample_data = {
        "_modules": {"tc": "TEST-CODE"},
        "alarms": [sample_alarm, sample_alarm, sample_alarm]
    }

    # populate db with duplicate records
    indexers.populate_alarms(sample_data)

    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            module_test = cursor.execute("""
                SELECT * FROM alarm_module
                WHERE code = %s;
            """, [sample_alarm["code"].split(settings.alarm_delim)[1]],).fetchall()

            alarm_code_sections = sample_alarm["code"].split(settings.alarm_delim)

            # verify 1 insertion made
            expected_module_code = alarm_code_sections[1]
            assert (len(module_test) == 1)
            assert any((module["code"] == expected_module_code) and (module["title"] == sample_alarm["domain"]) for module in module_test)

            expected_sequence = alarm_code_sections[2]
            expected_origin = alarm_code_sections[0]
            code_test = cursor.execute("""
                SELECT * from alarm_code
                WHERE alarm_sequence = %s AND origin = %s AND module = %s;
            """, (expected_sequence, expected_origin, module_test[0]["id"]),).fetchall()

            assert (len(code_test) == 1)
            assert any(entry["title"] == sample_alarm["title"] for entry in code_test)
            assert any(entry["severity_score"] == sample_alarm["severity"] for entry in code_test)
            assert any(entry["severity_category"] == sample_alarm["severity_category"].lower() for entry in code_test)
            assert any(entry["alarm_text"] == sample_alarm["alarm_text"] for entry in code_test)

def test_multiple_alarm_insert():
    settings = get_settings()
    # sample alarms with random codes and fields
    sample_alarm1 = {
        "code": f"am{settings.alarm_delim}tc{settings.alarm_delim}001", "title": "Test Alarm Code Title", "domain": "TEST-CODE", "severity": 200, 
        "severity_category": "Info", "alarm_text": "Further description of the alarm", "data_fields": {} }
    sample_alarm2 = {
        "code": f"am{settings.alarm_delim}tc{settings.alarm_delim}005", "title": "Test Code 5", "domain": "TEST-CODE", "severity": 1, 
        "severity_category": "Debug", "alarm_text": "More descriptions of the alarm...", "data_fields": { "program": "hello.cpp", "line": 5 } }
    sample_alarm3 = {
        "code": f"am{settings.alarm_delim}ot{settings.alarm_delim}944", "title": "Other Test Alarm", "domain": "OTHER-TEST", "severity": 500, 
        "severity_category": "Warning", "alarm_text": "Other descriptions of an alarm", "data_fields": { "axes": ["X", "Y", "Z"] } }
    sample_alarm4 = {
        "code": f"am{settings.alarm_delim}ta{settings.alarm_delim}023", "title": "Test Alarm Code Title", "domain": "TEST-ALARM", "severity": 833, 
        "severity_category": "Error", "alarm_text": "A random test alarm", "data_fields": {} }
    sample_alarm5 = {
        "code": f"am{settings.alarm_delim}nw{settings.alarm_delim}102", "title": "Network Connection Timeout", "domain": "NETWORK", "severity": 900, 
        "severity_category": "Error", "alarm_text": "Failed to establish connection with remote gateway after 3 retries.", "data_fields": { "ip_address": "192.168.1.50", "port": 443 } }
    sample_alarm6 = {
        "code": f"am{settings.alarm_delim}hw{settings.alarm_delim}310", "title": "Temperature Sensor Warning", "domain": "HARDWARE", "severity": 600, 
        "severity_category": "Warning", "alarm_text": "CPU core temperature exceeded nominal operational threshold.", "data_fields": { "sensor_id": "temp_cpu_2", "temperature_celsius": 88.5 } }
    sample_alarm7 = {
        "code": f"tt{settings.alarm_delim}db{settings.alarm_delim}014", "title": "Database Query Slowdown", "domain": "DATABASE", "severity": 400, 
        "severity_category": "Info", "alarm_text": "Execution time for transaction batch exceeded 5000ms.", "data_fields": { "query_id": "q_98234", "duration_ms": 5210 } }
    sample_alarm8 = {
        "code": f"tt{settings.alarm_delim}sec{settings.alarm_delim}088", "title": "Unauthorized Access Attempt", "domain": "SECURITY", "severity": 950, 
        "severity_category": "Error", "alarm_text": "Multiple failed authentication attempts detected from source.", "data_fields": { "attempts": 5, "username": "admin" } }
    sample_alarm9 = {
        "code": f"am{settings.alarm_delim}io{settings.alarm_delim}215", "title": "Disk Space Low", "domain": "STORAGE", "severity": 700, 
        "severity_category": "Warning", "alarm_text": "Available disk space on primary volume has dropped below 10%.", "data_fields": { "mount_point": "/var/log", "free_space_gb": 4.2 } }
    sample_alarm10 = {
        "code": f"tt{settings.alarm_delim}srv{settings.alarm_delim}003", "title": "Service Heartbeat Received", "domain": "SERVICE", "severity": 1, 
        "severity_category": "Debug", "alarm_text": "Routine ping received successfully from worker node.", "data_fields": { "node_id": "worker-04", "uptime_hours": 120 } }

    sample_data = {
        "_modules": {
            "tc": "TEST-CODE", "ot": "OTHER-TEST", "ta": "TEST-ALARM", "nw": "NETWORK", 
            "hw": "HARDWARE", "db": "DATABASE", "sec": "SECURITY", "io": "STORAGE", "srv": "SERVICE"
        },
        "_severity_scale": {
            "description": "Severity is an integer 1-1000, subdivided into bands with the default values shown.",
            "bands": { "Debug": 1, "Info": 167, "Warning": 500, "Error": 833, "Fatal": 1000 }
        },
        "alarms": [sample_alarm1, sample_alarm2, sample_alarm3, sample_alarm4, sample_alarm5, 
                   sample_alarm6, sample_alarm7, sample_alarm8, sample_alarm9, sample_alarm10]
    }

    # populate db with multiple records
    indexers.populate_alarms(sample_data)

    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            
            # loop through all inserted alarms to verify each one
            for alarm in sample_data["alarms"]:
                parts = alarm["code"].split(settings.alarm_delim)
                expected_origin = parts[0]
                expected_module_code = parts[1]
                expected_sequence = parts[2]

                module_test = cursor.execute("""
                    SELECT * FROM alarm_module
                    WHERE code = %s;
                """, [expected_module_code],).fetchall()

                # check that module was created/exists
                assert (len(module_test) >= 1)
                assert any((module["code"] == expected_module_code) and (module["title"] == alarm["domain"]) for module in module_test)

                module_id = module_test[0]["id"]
                
                code_test = cursor.execute("""
                    SELECT * from alarm_code
                    WHERE alarm_sequence = %s AND origin = %s AND module = %s;
                """, (expected_sequence, expected_origin, module_id),).fetchall()

                assert (len(code_test) >= 1), f"Alarm code entry missing for {alarm['code']}"
                assert any(entry["title"] == alarm["title"] for entry in code_test)
                assert any(entry["severity_score"] == alarm["severity"] for entry in code_test)
                assert any(entry["severity_category"] == alarm["severity_category"].lower() for entry in code_test)
                assert any(entry["alarm_text"] == alarm["alarm_text"] for entry in code_test)

def test_invalid_input():
    settings = get_settings()
    # empty code test
    with pytest.raises(indexers.InvalidInputError):
        invalid_alarm = {
            "code": "", "title": "Test Alarm Code Title", "domain": "TEST-CODE", "severity": 200,
            "severity_category": "Info", "alarm_text": "Further description of the alarm", "data_fields": {}
        }

        invalid_data = { "_modules": {}, "alarms": [invalid_alarm] }
        indexers.populate_alarms(invalid_data)

    # invalid code test
    with pytest.raises(indexers.InvalidInputError):
        invalid_alarm = {
            "code": f"{settings.alarm_delim}{settings.alarm_delim}", "title": "Test Alarm Code Title", "domain": "TEST-CODE", "severity": 200,
            "severity_category": "Info", "alarm_text": "Further description of the alarm", "data_fields": {}
        }

        invalid_data = { "_modules": {}, "alarms": [invalid_alarm] }
        indexers.populate_alarms(invalid_data)

    # empty fields test
    with pytest.raises(indexers.InvalidInputError):
        empty_alarm = { "code": "", "title": "", "domain": "", "severity": 1, "severity_category": "", "alarm_text": "", "data_fields": {} }

        invalid_data = { "_modules": {}, "alarms": [empty_alarm] }
        indexers.populate_alarms(invalid_data)

    # invalid severity score test
    with pytest.raises(indexers.InvalidInputError):
        invalid_severity_score = {
            "code": f"am{settings.alarm_delim}tc{settings.alarm_delim}001", "title": "Test Alarm Code Title", "domain": "TEST-CODE", "severity": -200, 
            "severity_category": "Info", "alarm_text": "Further description of the alarm", "data_fields": {}
        }

        invalid_data = { "_modules": {"tc": "TEST-CODE"}, "alarms": [invalid_severity_score] }
        indexers.populate_alarms(invalid_data)

# replace the temporary file open with the actual submodule once implemented
def validate_alarms_insert():
    import json 

    alarm_filepath: str = "docs/docs-proto/starter-kit/alarms/alarms.sample.json"
    with open(alarm_filepath, 'r', encoding='utf-8') as file:
        alarms_json = json.load(file)

    assert alarms_json != {}

    indexers.populate_alarms(alarms_json)

    settings = get_settings()
    with psycopg.connect(settings.postgres_dsn, row_factory=dict_row) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            # validate _modules populated correctly
            for module in alarms_json["_modules"]:
                res = cursor.execute("""
                    SELECT * FROM alarm_module
                    WHERE code = %s;
                """,
                [module]).fetchone()

                assert(res["code"] == module)
                assert(res["title"] == alarms_json["_modules"][module])

            # validate alarms populated correctly
            for alarm in alarms_json["alarms"]:
                alarm_code = alarm["code"]
                parts = alarm_code.split(settings.alarm_delim)

                res = cursor.execute("""
                    SELECT 
                        ac.origin AS origin,
                        am.code AS module,
                        ac.sequence AS sequence,
                        am.title AS domain,
                        am.severity_score AS severity_score,
                        am.severity_category AS severity_category,
                        am.alarm_text AS alarm_text,
                        am.data_fields AS data_fields
                    FROM alarm_code AS ac
                    INNER JOIN alarm_module AS am
                    ON ac.module = am.id
                    WHERE ac.origin = %s AND am.code = %s AND ac.sequence = %s;
                """,
                [parts[0], parts[1], parts[2]]).fetchone()

                # validate all fields
                assert(len(res) > 0)
                assert(f"{res["origin"]}{settings.alarm_delim}{res["module"]}{settings.alarm_delim}{res["sequence"]}" == alarm["code"])
                assert(res["domain"] == alarm["domain"])
                assert(res["severity_score"] == alarm["severity"])
                assert(res["severity_category"].lower() == alarm["severity_category"].lower())
                assert(res["alarm_text"] == alarm["alarm_text"])
                assert(res["data_fields"] == alarm["data_fields"])