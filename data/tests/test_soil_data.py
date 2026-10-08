import duckdb

def test_parquet_row_counts():
    raw_query = """
    SELECT COUNT(*) FROM read_csv('raw/soil-nutrient-analysis.csv', quote='"', ignore_errors=true, header=true)
    WHERE LOWER(state_name) LIKE '%haryana%'
    """
    raw_count = duckdb.query(raw_query).fetchone()[0]
    
    parquet_count = duckdb.query("SELECT COUNT(*) FROM 'processed/soil_haryana.parquet'").fetchone()[0]
    
    assert raw_count == parquet_count, f"Raw count {raw_count} != Parquet count {parquet_count}"
