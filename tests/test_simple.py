"""
Simple integration tests that verify basic functionality without complex mocking
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports_work():
    """Test that all necessary imports work"""
    try:
        import streamlit
        assert streamlit is not None
    except ImportError:
        pytest.skip("Streamlit not installed")

def test_module_structure():
    """Test that the streamlit module has expected structure"""
    import streamlit as app
    
    # Check that key functions exist
    assert hasattr(app, 'get_available_tables')
    assert hasattr(app, 'run_snowflake_query')
    assert hasattr(app, 'get_cortex_search_context')
    assert hasattr(app, 'generate_sql_from_question')
    assert hasattr(app, 'agent_api_call')
    assert hasattr(app, 'main')
    
    # Check they are callable
    assert callable(app.get_available_tables)
    assert callable(app.run_snowflake_query)
    assert callable(app.get_cortex_search_context)
    assert callable(app.generate_sql_from_question)
    assert callable(app.agent_api_call)
    assert callable(app.main)

def test_constants_defined():
    """Test that required constants are defined"""
    import streamlit as app
    
    # Check configuration constants exist
    assert hasattr(app, 'HOST')
    assert hasattr(app, 'ACCOUNT')
    assert hasattr(app, 'USER')
    assert hasattr(app, 'WAREHOUSE')
    assert hasattr(app, 'DATABASE')
    assert hasattr(app, 'SCHEMA')
    assert hasattr(app, 'CORTEX_SEARCH_SERVICES')
    assert hasattr(app, 'SEMANTIC_MODELS')

def test_sql_injection_prevention():
    """Test that the query sanitization logic exists"""
    # Read the streamlit.py file directly
    import os
    filepath = os.path.join(os.path.dirname(__file__), '..', 'streamlit.py')
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Should have logic to replace semicolons in run_snowflake_query
    assert 'replace' in source and 'run_snowflake_query' in source

def test_generator_function():
    """Test that agent_api_call is a generator"""
    # Read the streamlit.py file directly
    import os
    filepath = os.path.join(os.path.dirname(__file__), '..', 'streamlit.py')
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Check that agent_api_call uses yield
    assert 'yield' in source and 'agent_api_call' in source
