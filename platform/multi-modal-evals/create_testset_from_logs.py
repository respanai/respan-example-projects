import json
from .testsets import create_testset, create_testset_rows
from .logs import get_logs
from .constants import EVAL_RUN_FILTER_KEY, EVAL_RUN_ID, EVAL_RUN_METADATA_KEY
from datetime import datetime, timedelta


def extract_variables_from_logs(logs_data):
    """Extract test variables from logs for testset creation"""
    testset_rows = []
    
    for log in logs_data.get('results', []):
        respan_params = log.get('respan_params', {})
        variables = respan_params.get('variables', {})
        
        # Extract the relevant variables for our travel agent
        if 'category' in variables and 'name' in variables:
            row_data = {
                "category": variables.get('category'),
                "name": variables.get('name'), 
                "is_booking_hotel": variables.get('is_booking_hotel', False),
                "is_checking_weather": variables.get('is_checking_weather', False),
                "has_image": 'image' in variables,
                "customer_id": respan_params.get('customer_identifier', ''),
                "eval_run": (log.get('metadata') or {}).get(EVAL_RUN_METADATA_KEY, '')
            }
            
            # Add expected behavior based on variables
            expected_tools = []
            if variables.get('category'):
                expected_tools.append('search_places')
            if variables.get('is_booking_hotel'):
                expected_tools.append('find_hotels')
            if variables.get('is_checking_weather'):
                expected_tools.append('check_weather')
            
            row_data["expected_tools"] = ','.join(expected_tools)
            
            testset_rows.append({
                "row_data": row_data
            })
    
    return testset_rows


def create_travel_agent_testset():
    """Create a testset from travel agent logs"""
    
    # Fetch recent logs tagged with our eval run
    logs = get_logs(
        start_time=datetime.now() - timedelta(days=1),
        end_time=datetime.now(),
        filters={
            EVAL_RUN_FILTER_KEY: {
                "value": EVAL_RUN_ID,
            },
        },
    )
    
    if not logs:
        print("No logs found!")
        return None
    
    print(f"Found {len(logs.get('results', []))} logs")
    
    # Create testset
    testset = create_testset(
        name="Travel Agent Multi-Modal Testset",
        description="Test dataset for travel agent with multi-modal inputs and tool calls",
        column_definitions=[
            {"field": "category"},
            {"field": "name"}, 
            {"field": "is_booking_hotel"},
            {"field": "is_checking_weather"},
            {"field": "has_image"},
            {"field": "customer_id"},
            {"field": "eval_run"},
            {"field": "expected_tools"}
        ]
    )
    
    if not testset:
        print("Failed to create testset!")
        return None
    
    print(f"Created testset: {testset['name']} (ID: {testset['id']})")
    
    # Extract rows from logs
    testset_rows = extract_variables_from_logs(logs)
    
    if testset_rows:
        rows_result = create_testset_rows(testset["id"], testset_rows)
        if rows_result:
            print(f"Added {len(testset_rows)} rows to testset")
        else:
            print("Failed to add rows to testset")
    else:
        print("No valid rows extracted from logs")
    
    return testset


if __name__ == "__main__":
    testset = create_travel_agent_testset()
    if testset:
        print(f"\nTestset created successfully!")
        print(f"Name: {testset['name']}")
        print(f"ID: {testset['id']}")
        print(f"Columns: {len(testset.get('column_definitions', []))}")
    else:
        print("Failed to create testset from logs")
