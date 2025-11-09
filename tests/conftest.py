"""
Pytest configuration and shared fixtures
"""
import sys
from unittest.mock import MagicMock

# Mock Snowflake and Streamlit modules at the pytest session level
# This ensures they're mocked before any test imports them

def pytest_configure(config):
    """
    Configure pytest and set up global mocks
    """
    # Mock snowflake modules
    sys.modules['snowflake'] = MagicMock()
    sys.modules['snowflake.connector'] = MagicMock()
    sys.modules['snowflake.connector.cursor'] = MagicMock()
    sys.modules['snowflake.connector.errors'] = MagicMock()
    
    # Mock streamlit if needed for imports
    if 'streamlit' not in sys.modules:
        mock_streamlit = MagicMock()
        mock_streamlit.secrets = {
            'snowflake': {
                'host': 'test.snowflakecomputing.com',
                'account': 'test_account',
                'user': 'test_user',
                'password': 'test_password',
                'role': 'test_role'
            }
        }
        sys.modules['streamlit'] = mock_streamlit