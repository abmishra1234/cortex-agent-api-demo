import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the actual module
import streamlit as streamlit_app

@pytest.fixture
def mock_streamlit():
    """Fixture to mock Streamlit module and session state"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    with patch.object(streamlit_app.st, "session_state", create=True) as mock_session:
        mock_session.CONN = mock_conn
        yield mock_session, mock_cursor

def test_streamlit_app_functionality():
    """Test basic app structure"""
    assert callable(streamlit_app.main)
    assert hasattr(streamlit_app, "get_available_tables")
    assert hasattr(streamlit_app, "run_snowflake_query")
