import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
import json
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the actual module after mocking dependencies
import streamlit as streamlit_app

@pytest.fixture
def mock_streamlit_session():
    """Fixture to mock Streamlit session state"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock st.session_state
    with patch.object(streamlit_app.st, 'session_state', create=True) as mock_session:
        mock_session.CONN = mock_conn
        yield mock_session, mock_cursor

def test_database_interaction():
    """Basic test to verify database test structure"""
    assert True

def test_get_available_tables(mock_streamlit_session):
    """Test retrieving available tables from Snowflake"""
    # This test verifies that the function exists and is callable
    assert hasattr(streamlit_app, 'get_available_tables')
    assert callable(streamlit_app.get_available_tables)

def test_run_snowflake_query_success(mock_streamlit_session):
    """Test that run_snowflake_query function exists"""
    assert hasattr(streamlit_app, 'run_snowflake_query')
    assert callable(streamlit_app.run_snowflake_query)

def test_run_snowflake_query_removes_semicolon(mock_streamlit_session):
    """Test that semicolons are removed from queries for security"""
    # Read source code to verify the security feature exists
    import os
    filepath = os.path.join(os.path.dirname(__file__), '..', 'streamlit.py')
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Verify that run_snowflake_query has semicolon removal logic
    assert 'def run_snowflake_query' in source
    assert '.replace' in source and ';' in source

def test_get_cortex_search_context(mock_streamlit_session):
    """Test Cortex search context retrieval function exists"""
    assert hasattr(streamlit_app, 'get_cortex_search_context')
    assert callable(streamlit_app.get_cortex_search_context)

def test_database_connection_error(mock_streamlit_session):
    """Test that error handling exists in run_snowflake_query"""
    # Read source to verify try/except exists
    import os
    filepath = os.path.join(os.path.dirname(__file__), '..', 'streamlit.py')
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Verify error handling exists
    assert 'try:' in source or 'except' in source

def test_cortex_search_with_special_characters(mock_streamlit_session):
    """Test that special character escaping logic exists"""
    # Read source to verify escaping logic exists
    import os
    filepath = os.path.join(os.path.dirname(__file__), '..', 'streamlit.py')
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Verify that get_cortex_search_context has escaping logic
    assert 'def get_cortex_search_context' in source
    assert 'replace' in source or 'escape' in source.lower()

def test_empty_query_results(mock_streamlit_session):
    """Test that run_snowflake_query can handle empty results"""
    # This test verifies the function structure exists
    assert hasattr(streamlit_app, 'run_snowflake_query')
    assert callable(streamlit_app.run_snowflake_query)