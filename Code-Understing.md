# Snowflake Cortex Agent - Detailed Code Structure Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Details](#component-details)
3. [Data Flow](#data-flow)
4. [Setup Instructions](#setup-instructions)
5. [Testing Guide](#testing-guide)
6. [Development Guidelines](#development-guidelines)

## Architecture Overview

This application is an Intelligent Sales Assistant built using Snowflake's Cortex AI capabilities and Streamlit for the frontend. It allows users to ask natural language questions about sales data and get AI-generated SQL queries with interpreted results.

### High-Level Architecture Diagram

![alt text](image.png)

### Component Architecture Diagram

![alt text](image-1.png)

### Data Flow Diagram

![alt text](image-2.png)

### Sequence Diagram: User Query Flow

![alt text](image-3.png)

## Component Details

### 1. streamlit.py - Main Application File

This is the core application file containing all the logic. Let's break it down:

#### A. Configuration Constants

```python
HOST = st.secrets["snowflake"]["host"]
ACCOUNT = st.secrets["snowflake"]["account"]
USER = st.secrets["snowflake"]["user"]
PASSWORD = st.secrets["snowflake"]["password"]
ROLE = st.secrets["snowflake"]["role"]
WAREHOUSE = "SALES_INTELLIGENCE_WH"
DATABASE = "SALES_INTELLIGENCE"
SCHEMA = "DATA"
CORTEX_SEARCH_SERVICES = "SALES_INTELLIGENCE.DATA.SALES_CONVERSATION_SEARCH"
SEMANTIC_MODELS = "sales_intelligence.data.models/sales_metrics_model.yaml"
```

**Purpose**: These constants define the Snowflake connection parameters and service locations.

**Key Points**:
- Credentials are loaded from `.streamlit/secrets.toml` (never hardcoded)
- Database and schema names match those created in `setup.sql`
- Cortex Search Service name references the search index created on transcripts

#### B. get_available_tables()

```python
def get_available_tables():
    """Get list of available tables in the schema"""
```

**Purpose**: Retrieves all tables from the specified Snowflake schema.

**Flow**:
1. Gets cursor from session state connection
2. Sets database and schema context
3. Executes `SHOW TABLES` command
4. Returns list of table names

**Usage**: Called to show available tables in sidebar and for SQL generation.

#### C. run_snowflake_query(query)

```python
def run_snowflake_query(query):
```

**Purpose**: Executes a SQL query against Snowflake and returns results.

**Flow**:
1. Gets cursor with DictCursor (returns results as dictionaries)
2. Sets database and schema context
3. Removes semicolons from query (security measure)
4. Executes query
5. Fetches all results
6. Returns results or None on error

**Security Note**: Removes semicolons to prevent SQL injection through query chaining.

#### D. get_cortex_search_context(query)

```python
def get_cortex_search_context(query: str):
    """Get relevant context from Cortex Search Service"""
```

**Purpose**: Searches through sales conversation transcripts using Cortex Search.

**Flow**:
1. Escapes special characters in the query
2. Calls `SNOWFLAKE.CORTEX.SEARCH_PREVIEW()` function
3. Passes query with limit of 5 results
4. Returns search results as list

**How Cortex Search Works**:
- Uses semantic search (meaning-based, not just keyword matching)
- Searches the `transcript_text` field in sales conversations
- Returns most relevant conversation excerpts

#### E. generate_sql_from_question(user_query, tables)

```python
def generate_sql_from_question(user_query: str, tables: list):
    """Use Cortex to generate SQL from natural language question"""
```

**Purpose**: Converts natural language questions into SQL queries using AI.

**Flow**:
1. Retrieves schema information for all tables
2. Builds a detailed prompt with:
   - Table names
   - Column names and types
   - User's question
   - Instructions for proper SQL generation
3. Calls `SNOWFLAKE.CORTEX.COMPLETE()` with 'mistral-large2' model
4. Cleans up the response (removes markdown formatting)
5. Returns generated SQL

**Example Transformation**:
- Input: "What was total sales last year?"
- Output: `SELECT SUM(DEAL_VALUE) FROM SALES_METRICS WHERE YEAR(CLOSE_DATE) = 2024`

#### F. agent_api_call(prompt, session_id)

```python
def agent_api_call(prompt: str, session_id: str):
    """Generator function that makes Cortex Agent call using COMPLETE function"""
```

**Purpose**: Main orchestrator function that handles the entire query workflow.

**This is a Generator Function** - it yields results incrementally for streaming.

**Flow**:
1. **Get Available Tables** - Retrieves list of tables
2. **Generate SQL** - Converts question to SQL using AI
3. **Execute Query** - Runs the generated SQL
4. **Get Search Context** - Finds relevant conversation transcripts
5. **Generate Interpretation** - Creates natural language explanation of results

**Streaming Behavior**:
```python
yield "🔍 Analyzing your question...\n\n"
# ... process ...
yield f"📝 **Generated SQL Query:**\n```sql\n{generated_sql}\n```\n\n"
# ... process ...
yield "💡 **Interpretation:**\n\n"
```

This creates a real-time, progressive display of results to the user.

#### G. main()

```python
def main():
```

**Purpose**: Entry point of the Streamlit application.

**Flow**:
1. **Sidebar Setup**:
   - Display connection information
   - Show available tables
   - Add "Reset Conversation" button

2. **Connection Management**:
   - Check if connection exists in session state
   - Create new connection if needed
   - Handle connection errors

3. **Session State Initialization**:
   - Initialize message history list

4. **Display Chat History**:
   - Loop through stored messages
   - Display each message with appropriate role (user/assistant)

5. **Handle User Input**:
   - Capture input from chat input box
   - Add user message to display and history
   - Call `agent_api_call()` as generator
   - Stream response to UI using `st.write_stream()`
   - Save assistant response to history

### 2. setup.sql - Database Setup Script

This SQL script creates and populates the Snowflake database.

#### Structure:

```sql
-- 1. Create database and schema
CREATE OR REPLACE DATABASE sales_intelligence;
CREATE OR REPLACE SCHEMA sales_intelligence.data;
CREATE OR REPLACE WAREHOUSE sales_intelligence_wh;

-- 2. Create tables
CREATE TABLE sales_conversations (...);
CREATE TABLE sales_metrics (...);

-- 3. Insert sample data
INSERT INTO sales_conversations VALUES (...);
INSERT INTO sales_metrics VALUES (...);

-- 4. Enable change tracking
ALTER TABLE sales_conversations SET CHANGE_TRACKING = TRUE;

-- 5. Create Cortex Search Service
CREATE OR REPLACE CORTEX SEARCH SERVICE sales_conversation_search
  ON transcript_text
  ATTRIBUTES customer_name, deal_stage, sales_rep
  WAREHOUSE = sales_intelligence_wh
  TARGET_LAG = '1 hour'
  AS (...);

-- 6. Create stage for models
CREATE OR REPLACE STAGE models DIRECTORY = (ENABLE = TRUE);
```

#### Key Components:

**sales_conversations table**:
- Stores detailed call transcripts
- Contains rich text data for semantic search
- Includes metadata (customer, deal stage, rep, date, value)

**sales_metrics table**:
- Stores structured deal data
- Win/loss status
- Financial metrics
- Timeline data

**Cortex Search Service**:
- Indexes conversation transcripts
- Enables semantic search
- Updates every hour (`TARGET_LAG = '1 hour'`)
- Searches on `transcript_text` field
- Returns attributes for context

### 3. sales_metrics_model.yaml - Semantic Model

This YAML file defines the semantic layer for the data model.

```yaml
name: sales_metrics
description: Sales metrics and analytics model
tables:
  - name: SALES_METRICS
    base_table:
      database: SALES_INTELLIGENCE
      schema: DATA
      table: SALES_METRICS
    dimensions: [...]
    time_dimensions: [...]
    measures: [...]
```

#### Purpose:
- Provides metadata about the data model
- Defines synonyms for natural language queries
- Describes business meaning of columns
- Includes sample values for context

#### Structure:

**Dimensions**: Categorical fields
- DEAL_ID, CUSTOMER_NAME, SALES_STAGE, etc.
- Each has synonyms (e.g., "client", "buyer" for CUSTOMER_NAME)

**Time Dimensions**: Date/time fields
- CLOSE_DATE with synonyms like "completion date", "sale date"

**Measures**: Numeric metrics
- DEAL_VALUE with synonyms like "revenue", "sale_amount"

### 4. Test Files

#### tests/test_streamlit_app.py
```python
def test_streamlit_app_functionality():
    assert True  # Placeholder
```

Currently contains placeholder tests that need to be implemented.

#### tests/test_database.py
```python
def test_database_interaction():
    assert True  # Placeholder
```

Placeholder for database interaction tests.

### 5. Configuration Files

#### .streamlit/secrets.toml
Stores Snowflake connection credentials (not checked into git):
```toml
[snowflake]
account = "your_account"
user = "your_user"
password = "your_password"
role = "your_role"
host = "your_host"
```

#### pytest.ini
Configures pytest behavior:
```ini
[pytest]
addopts = -v --tb=short
testpaths = tests
python_files = test_*.py
```

#### requirements.txt
Production dependencies:
- streamlit: Web framework
- snowflake-connector-python: Database connector
- requests: HTTP library
- sseclient: Server-sent events client

#### requirements-dev.txt
Development dependencies:
- pytest: Testing framework
- pytest-cov: Coverage reporting
- pytest-mock: Mocking utilities

## Data Flow

Let's trace a complete user query through the system:

### Example: "What was the total sales volume last year?"

**Step 1: User Input**
```
User types: "What was the total sales volume last year?"
↓
Streamlit captures input
↓
Calls agent_api_call(prompt="What was the total sales volume last year?", session_id="session_1")
```

**Step 2: Get Available Tables**
```
agent_api_call() calls get_available_tables()
↓
Executes: SHOW TABLES
↓
Returns: ["SALES_CONVERSATIONS", "SALES_METRICS"]
```

**Step 3: Generate SQL**
```
Calls generate_sql_from_question("What was the total sales volume last year?", tables)
↓
Gets table schemas:
  SALES_METRICS: DEAL_ID, CUSTOMER_NAME, DEAL_VALUE, CLOSE_DATE, ...
↓
Builds prompt:
  "You are a SQL expert. Generate SQL query...
   Database Schema:
   Table: SALES_METRICS
   Columns: DEAL_ID (VARCHAR), DEAL_VALUE (FLOAT), CLOSE_DATE (DATE)...
   User Question: What was the total sales volume last year?"
↓
Calls Cortex COMPLETE with 'mistral-large2'
↓
Returns: "SELECT SUM(DEAL_VALUE) AS total_sales FROM SALES_METRICS WHERE YEAR(CLOSE_DATE) = 2024"
```

**Step 4: Execute SQL**
```
Calls run_snowflake_query(generated_sql)
↓
Executes: SELECT SUM(DEAL_VALUE) AS total_sales FROM SALES_METRICS WHERE YEAR(CLOSE_DATE) = 2024
↓
Returns: [{"total_sales": 840000}]
```

**Step 5: Get Search Context**
```
Calls get_cortex_search_context("What was the total sales volume last year?")
↓
Executes: CORTEX.SEARCH_PREVIEW with query
↓
Returns: [] (no relevant conversations)
```

**Step 6: Generate Interpretation**
```
Builds interpretation prompt:
  "Based on the SQL query results below...
   Query Results: 1. {"total_sales": 840000}
   Provide natural language summary..."
↓
Calls Cortex COMPLETE
↓
Returns: "The total sales volume for last year was $840,000. This represents
         the sum of all deal values that were closed in 2024..."
```

**Step 7: Stream to User**
```
Yields results in chunks:
  "🔍 Analyzing your question..."
  "📝 Generated SQL Query: SELECT SUM(DEAL_VALUE)..."
  "⚙️ Executing query..."
  "📊 Query Results: Found 1 rows..."
  "💡 Interpretation: The total sales volume..."
```

## Setup Instructions

See the [Building on Windows](#building-on-windows) section below.

## Testing Guide

See the [Testing Guide](#testing-your-code) section below.

## Development Guidelines

### Adding New Features

1. **New Database Function**:
   - Add function to `streamlit.py`
   - Use existing cursor pattern
   - Handle errors gracefully
   - Add docstring

2. **New AI Capability**:
   - Use `SNOWFLAKE.CORTEX.COMPLETE()` pattern
   - Escape user input properly
   - Build clear prompts
   - Handle response parsing

3. **New UI Component**:
   - Follow Streamlit patterns
   - Use session state for persistence
   - Add to sidebar or main area
   - Maintain chat-like interface

### Code Organization Tips

- Keep connection management in session state
- Use generator functions for streaming
- Separate concerns (DB, AI, UI)
- Add error handling everywhere
- Use type hints where possible

### Best Practices

1. **Security**:
   - Never commit `secrets.toml`
   - Escape SQL inputs
   - Validate user input
   - Use parameterized queries where possible

2. **Performance**:
   - Cache Snowflake connections
   - Limit search results
   - Use generators for streaming
   - Close cursors after use

3. **User Experience**:
   - Show progress indicators
   - Stream results for responsiveness
   - Display SQL for transparency
   - Handle errors gracefully

4. **Testing**:
   - Mock Snowflake connections
   - Test each function independently
   - Test error cases
   - Test with various inputs

---

## Building on Windows

### Prerequisites

1. **Python 3.8 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify installation:
     ```powershell
     python --version
     ```

2. **Git** (optional, for cloning)
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify installation:
     ```powershell
     git --version
     ```

3. **Snowflake Account**
   - Sign up at [signup.snowflake.com](https://signup.snowflake.com/)
   - Note down your account details

### Step-by-Step Setup

#### Step 1: Clone or Download the Repository

**Option A: Using Git**
```powershell
git clone <repository-url>
cd cortex-agent-api-demo
```

**Option B: Download ZIP**
- Download the repository as ZIP
- Extract to a folder like `C:\Projects\cortex-agent-api-demo`
- Open PowerShell and navigate to that folder

#### Step 2: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

**If you get an execution policy error**, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Step 3: Install Dependencies

```powershell
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

#### Step 4: Setup Snowflake Database

1. **Log into Snowflake**:
   - Go to your Snowflake account URL
   - Navigate to `Projects` → `Worksheets`
   - Click `Create SQL Worksheet`

2. **Run Setup Script**:
   - Open [`setup.sql`](setup.sql) in your text editor
   - Copy the entire contents
   - Paste into the Snowflake worksheet
   - Click "Run All" or press `Ctrl+Enter`
   - Wait for all steps to complete (may take 2-3 minutes)

3. **Upload Semantic Model**:
   - In Snowflake, go to `Data` → `Add Data` → `Load files into a Stage`
   - Upload [`sales_metrics_model.yaml`](sales_metrics_model.yaml)
   - Select:
     - Database: `SALES_INTELLIGENCE`
     - Schema: `DATA`
     - Stage: `MODELS`
   - Click "Upload"

#### Step 5: Configure Secrets

1. **Create `.streamlit` folder** (if it doesn't exist):
   ```powershell
   mkdir .streamlit
   ```

2. **Create `secrets.toml` file**:
   ```powershell
   New-Item -Path ".\.streamlit\secrets.toml" -ItemType File
   ```

3. **Get Snowflake Connection Details**:
   - In Snowflake, click your name (bottom left)
   - Select "Connect a tool to Snowflake"
   - Note down the details

4. **Edit `secrets.toml`**:
   Open `.streamlit\secrets.toml` in a text editor and add:
   ```toml
   [snowflake]
   account = "your_account_identifier"
   user = "your_username"
   password = "your_password"
   role = "your_role"
   host = "your_account_url.snowflakecomputing.com"
   ```

   **Replace** the placeholder values with your actual Snowflake credentials.

   **Example**:
   ```toml
   [snowflake]
   account = "abc12345.us-east-1"
   user = "JOHN_DOE"
   password = "MySecureP@ssw0rd!"
   role = "ACCOUNTADMIN"
   host = "abc12345.us-east-1.snowflakecomputing.com"
   ```

#### Step 6: Run the Application

```powershell
streamlit run streamlit.py
```

Your default browser should open automatically to `http://localhost:8501`.

**If it doesn't open**, manually navigate to: `http://localhost:8501`

#### Step 7: Test the Application

Try these sample queries in the chat interface:

1. **SQL Generation Test**:
   ```
   What was the total sales volume last year?
   ```
   Expected: SQL query generation + results + interpretation

2. **Search Test**:
   ```
   Summarize the call with TechCorp Inc
   ```
   Expected: Summary of the conversation transcript

3. **Complex Query Test**:
   ```
   Which sales rep had the highest deal value?
   ```
   Expected: SQL query + results showing the top sales rep

### Troubleshooting

#### Error: "Module not found"
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

#### Error: "Connection not established"
- Check your `secrets.toml` file
- Verify Snowflake credentials
- Ensure Snowflake account is active
- Check firewall settings

#### Error: "Table not found"
- Verify `setup.sql` was run completely
- Check database and schema names in Snowflake
- Ensure you have proper permissions

#### Port already in use
```powershell
# Run on a different port
streamlit run streamlit.py --server.port 8502
```

---

## Testing Your Code

### Understanding the Test Setup

The tests use **mocking** to avoid needing actual Snowflake connections. This is done through:

1. **conftest.py** - Global test configuration that mocks Snowflake modules
2. **Test fixtures** - Reusable mock objects for each test
3. **unittest.mock** - Python's built-in mocking library

### Running Existing Tests

#### Prerequisites

Make sure you're in your virtual environment:
```powershell
# If not already activated
.\venv\Scripts\Activate.ps1
```

#### Run All Tests
```powershell
pytest
```

Output should look like:
```
====================== test session starts ======================
platform win32 -- Python 3.11.7, pytest-8.4.2, pluggy-1.6.0
collected 9 items

tests/test_database.py ........                           [ 88%]
tests/test_streamlit_app.py .                             [100%]

====================== 9 passed in 0.45s ======================
```

#### Run with Verbose Output
```powershell
pytest -v
```

#### Run with Print Statements Visible
```powershell
pytest -v -s
```

#### Run with Coverage Report
```powershell
pytest --cov=. --cov-report=html --cov-report=term
```

This generates:
- Terminal output showing coverage percentages
- HTML report in `htmlcov/index.html`

#### View HTML Coverage Report
```powershell
start htmlcov\index.html
```

#### Run Specific Test File
```powershell
# Test database functions only
pytest tests\test_database.py

# Test streamlit app only
pytest tests\test_streamlit_app.py
```

#### Run Specific Test Function
```powershell
pytest tests\test_database.py::test_get_available_tables
```

#### Run Tests Matching a Pattern
```powershell
# Run all tests with 'database' in the name
pytest -k "database"

# Run all tests with 'sql' in the name
pytest -k "sql"
```

### Test File Structure

```
tests/
├── conftest.py              # Global configuration and fixtures
├── test_database.py         # Database interaction tests
└── test_streamlit_app.py    # Application logic tests
```

### Understanding Mock Objects

**What is Mocking?**
Mocking replaces real objects with fake ones for testing. This allows you to:
- Test without external dependencies (databases, APIs)
- Control what functions return
- Verify that functions were called correctly

**Example of a Mock**:
```python
# Real code would do this:
cursor.execute("SELECT * FROM table")
results = cursor.fetchall()

# In tests, we mock it:
mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'test'}]
```

### Current Test Coverage

#### tests/test_database.py

✅ **test_database_interaction** - Basic placeholder test
✅ **test_get_available_tables** - Tests table retrieval
✅ **test_run_snowflake_query_success** - Tests successful query execution
✅ **test_run_snowflake_query_removes_semicolon** - Tests SQL injection prevention
✅ **test_get_cortex_search_context** - Tests search functionality
✅ **test_database_connection_error** - Tests error handling
✅ **test_cortex_search_with_special_characters** - Tests input escaping
✅ **test_empty_query_results** - Tests empty result handling

#### tests/test_streamlit_app.py

✅ **test_generate_sql_from_question_basic** - Tests SQL generation
✅ **test_generate_sql_handles_markdown_formatting** - Tests markdown stripping
✅ **test_agent_api_call_streams_results** - Tests streaming response
✅ **test_main_initializes_session_state** - Tests main function structure
✅ **test_chat_message_history_persistence** - Tests message structure

### Adding New Test Cases

#### Step 1: Choose the Right File

- **test_database.py** - For database queries, connections, Snowflake interactions
- **test_streamlit_app.py** - For UI logic, chat functionality, agent behavior
- **test_new_feature.py** - Create new file for new major features

#### Step 2: Write Your Test

Follow the **AAA pattern**:
```python
def test_my_new_feature(mock_streamlit_session):
    """Clear description of what this test verifies"""
    # Arrange - Set up test data and mocks
    mock_session, mock_cursor = mock_streamlit_session
    mock_cursor.fetchall.return_value = [{'result': 'data'}]
    
    # Act - Call the function being tested
    from streamlit import my_function
    result = my_function("input")
    
    # Assert - Verify the results
    assert result is not None
    assert result == expected_value
    assert mock_cursor.execute.called
```

#### Step 3: Use Fixtures

Fixtures are reusable test components:

```python
@pytest.fixture
def sample_sales_data():
    """Provides sample sales data for tests"""
    return [
        {'deal_id': 1, 'value': 75000, 'customer': 'TechCorp'},
        {'deal_id': 2, 'value': 120000, 'customer': 'SecureBank'}
    ]

def test_with_fixture(sample_sales_data):
    """Use the fixture in your test"""
    assert len(sample_sales_data) == 2
    assert sample_sales_data[0]['value'] == 75000
```

#### Step 4: Mock External Calls

When testing functions that call other functions:

```python
from unittest.mock import patch

def test_agent_with_mocked_dependencies():
    """Test agent while mocking its dependencies"""
    with patch('streamlit.get_available_tables') as mock_tables, \
         patch('streamlit.generate_sql_from_question') as mock_gen_sql:
        
        # Set up what mocked functions should return
        mock_tables.return_value = ['SALES_METRICS']
        mock_gen_sql.return_value = 'SELECT * FROM SALES_METRICS'
        
        # Now test your function
        from streamlit import agent_api_call
        result = list(agent_api_call("test query", "session1"))
        
        # Verify mocked functions were called
        assert mock_tables.called
        assert mock_gen_sql.called
```

#### Step 5: Test Error Cases

Always test what happens when things go wrong:

```python
def test_handles_database_error(mock_streamlit_session):
    """Test that database errors are handled gracefully"""
    mock_session, mock_cursor = mock_streamlit_session
    
    # Make the cursor throw an error
    mock_cursor.execute.side_effect = Exception("Database connection lost")
    
    from streamlit import run_snowflake_query
    result = run_snowflake_query("SELECT * FROM table")
    
    # Should return None instead of crashing
    assert result is None
```

### Example: Adding a Complete Test Case

Let's say you added a new function to calculate average deal size:

```python
# In streamlit.py
def calculate_average_deal_size(product_line=None):
    """Calculate average deal size, optionally filtered by product line"""
    query = "SELECT AVG(DEAL_VALUE) as avg_size FROM SALES_METRICS"
    if product_line:
        query += f" WHERE PRODUCT_LINE = '{product_line}'"
    
    results = run_snowflake_query(query)
    if results and len(results) > 0:
        return results[0]['avg_size']
    return 0
```

Now add a test:

```python
# filepath: tests/test_database.py
# ...existing code...

def test_calculate_average_deal_size_all_products(mock_streamlit_session):
    """Test calculating average deal size for all products"""
    # Arrange
    mock_session, mock_cursor = mock_streamlit_session
    mock_cursor.fetchall.return_value = [{'avg_size': 97500.0}]
    
    # Act
    from streamlit import calculate_average_deal_size
    result = calculate_average_deal_size()
    
    # Assert
    assert result == 97500.0
    assert mock_cursor.execute.called

def test_calculate_average_deal_size_specific_product(mock_streamlit_session):
    """Test calculating average deal size for specific product line"""
    # Arrange
    mock_session, mock_cursor = mock_streamlit_session
    mock_cursor.fetchall.return_value = [{'avg_size': 85000.0}]
    
    # Act
    from streamlit import calculate_average_deal_size
    result = calculate_average_deal_size(product_line="Premium Security")
    
    # Assert
    assert result == 85000.0
    # Verify the WHERE clause was included
    call_args = str(mock_cursor.execute.call_args)
    assert 'Premium Security' in call_args

def test_calculate_average_deal_size_no_results(mock_streamlit_session):
    """Test handling of no results"""
    # Arrange
    mock_session, mock_cursor = mock_streamlit_session
    mock_cursor.fetchall.return_value = []
    
    # Act
    from streamlit import calculate_average_deal_size
    result = calculate_average_deal_size()
    
    # Assert
    assert result == 0
```

### Common Testing Patterns

#### 1. Testing Functions That Stream Data

```python
def test_streaming_function():
    """Test a generator function"""
    generator = my_streaming_function()
    
    # Verify it's a generator
    assert hasattr(generator, '__iter__')
    assert hasattr(generator, '__next__')
    
    # Collect all streamed data
    results = list(generator)
    
    # Verify content
    assert len(results) > 0
    assert "expected content" in ''.join(results)
```

#### 2. Testing Functions With Multiple Return Values

```python
def test_function_with_multiple_returns():
    """Test function that can return different things"""
    # Test success case
    result = my_function(valid_input)
    assert result is not None
    
    # Test error case
    result = my_function(invalid_input)
    assert result is None
```

#### 3. Testing JSON Parsing

```python
import json

def test_json_parsing(mock_streamlit_session):
    """Test parsing of JSON responses"""
    mock_session, mock_cursor = mock_streamlit_session
    
    json_data = json.dumps({'key': 'value', 'number': 42})
    mock_cursor.fetchone.return_value = {'JSON_FIELD': json_data}
    
    result = my_json_function()
    
    assert result['key'] == 'value'
    assert result['number'] == 42
```

### Troubleshooting Tests

#### Import Errors

**Error**: `ModuleNotFoundError: No module named 'snowflake'`

**Solution**: Make sure `conftest.py` is in the `tests/` directory. This file mocks Snowflake before imports.

#### Test Isolation Issues

**Problem**: Tests pass individually but fail when run together

**Solution**: Use fixtures and ensure each test cleans up:
```python
@pytest.fixture
def clean_session():
    """Provide a clean session for each test"""
    yield
    # Cleanup code here
```