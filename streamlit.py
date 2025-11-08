import json
import requests
import streamlit as st
import snowflake.connector # type: ignore
from snowflake.connector import DictCursor # type: ignore


# replace these values in your .streamlit.toml file, not here!
HOST = st.secrets["snowflake"]["host"]
ACCOUNT = st.secrets["snowflake"]["account"]
USER =st.secrets["snowflake"]["user"]
PASSWORD = st.secrets["snowflake"]["password"]
ROLE = st.secrets["snowflake"]["role"]
WAREHOUSE= "SALES_INTELLIGENCE_WH"
DATABASE = "SALES_INTELLIGENCE"
SCHEMA = "DATA"

# variables shared across pages
CORTEX_SEARCH_SERVICES = "SALES_INTELLIGENCE.DATA.SALES_CONVERSATION_SEARCH"
SEMANTIC_MODELS = "sales_intelligence.data.models/sales_metrics_model.yaml"

def get_available_tables():
    """Get list of available tables in the schema"""
    try:
        cursor = st.session_state.CONN.cursor(DictCursor)
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA}")
        
        sql = "SHOW TABLES"
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        
        tables = [row['name'] for row in results]
        return tables
    except Exception as e:
        st.error(f"Could not get tables: {str(e)}")
        return []

def run_snowflake_query(query):
    try:
        cursor = st.session_state.CONN.cursor(DictCursor)
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA}")
        cursor.execute(query.replace(';',''))
        results = cursor.fetchall()
        cursor.close()
        return results

    except Exception as e:
        st.error(f"Error executing SQL: {str(e)}")
        return None

def get_cortex_search_context(query: str):
    """Get relevant context from Cortex Search Service"""
    try:
        cursor = st.session_state.CONN.cursor(DictCursor)
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA}")
        
        # Properly escape and format the query for Cortex Search
        escaped_query = query.replace('"', '\\"').replace("'", "\\'")
        
        sql = f"""
        SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            '{CORTEX_SEARCH_SERVICES}',
            OBJECT_CONSTRUCT(
                'query', '{escaped_query}',
                'limit', 5
            )
        ) as search_results
        """
        
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        
        if result and 'SEARCH_RESULTS' in result:
            search_data = result['SEARCH_RESULTS']
            if isinstance(search_data, str):
                search_data = json.loads(search_data)
            return search_data.get('results', [])
        return []
    except Exception as e:
        st.warning(f"Could not retrieve search context: {str(e)}")
        return []

def generate_sql_from_question(user_query: str, tables: list):
    """Use Cortex to generate SQL from natural language question"""
    try:
        cursor = st.session_state.CONN.cursor(DictCursor)
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA}")
        
        # Get table schemas
        table_schemas = {}
        for table in tables:
            cursor.execute(f"DESCRIBE TABLE {table}")
            columns = cursor.fetchall()
            table_schemas[table] = [{"name": col["name"], "type": col["type"]} for col in columns]
        
        # Build prompt for SQL generation
        schema_info_parts = []
        for table, cols in table_schemas.items():
            col_info = ', '.join([f"{col['name']} ({col['type']})" for col in cols])
            schema_info_parts.append(f"Table: {table}\nColumns: {col_info}")
        
        schema_info = "\n".join(schema_info_parts)
        
        prompt = f"""You are a SQL expert. Generate a SQL query to answer the user's question.

Database Schema:
{schema_info}

User Question: {user_query}

Generate ONLY the SQL query without any explanation or markdown formatting. The query should:
1. Use proper Snowflake SQL syntax
2. Reference the correct table and column names
3. Handle date/time operations correctly (use YEAR(), DATEADD(), etc.)
4. Return meaningful results

SQL Query:"""
        
        escaped_prompt = prompt.replace("'", "''")
        
        sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large2',
            '{escaped_prompt}'
        ) as sql_query
        """
        
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        
        if result and 'SQL_QUERY' in result:
            generated_sql = result['SQL_QUERY'].strip()
            # Clean up any markdown formatting
            generated_sql = generated_sql.replace('```sql', '').replace('```', '').strip()
            return generated_sql
        return None
        
    except Exception as e:
        st.error(f"Error generating SQL: {str(e)}")
        return None

def agent_api_call(prompt: str, session_id: str):
    """Generator function that makes Cortex Agent call using COMPLETE function"""
    try:
        # Get available tables first
        tables = get_available_tables()
        
        if not tables:
            yield "No tables found in the database. Please check your database configuration."
            return
        
        # Step 1: Generate SQL from the question
        yield "🔍 Analyzing your question...\n\n"
        
        generated_sql = generate_sql_from_question(prompt, tables)
        
        if not generated_sql:
            yield "❌ Could not generate SQL query from your question."
            return
        
        yield f"📝 **Generated SQL Query:**\n```sql\n{generated_sql}\n```\n\n"
        
        # Step 2: Execute the SQL query
        yield "⚙️ Executing query...\n\n"
        
        query_results = run_snowflake_query(generated_sql)
        
        if query_results is None:
            yield "❌ Error executing the query."
            return
        
        if not query_results:
            yield "📊 **Query Results:** No data found.\n\n"
            result_context = "No results returned from the query."
        else:
            yield f"📊 **Query Results:** Found {len(query_results)} rows.\n\n"
            
            # Format results for display
            result_context = "Query Results:\n"
            for idx, row in enumerate(query_results[:10], 1):
                result_context += f"{idx}. {json.dumps(dict(row), default=str)}\n"
        
        # Step 3: Get search context
        search_results = get_cortex_search_context(prompt)
        
        context = result_context
        
        if search_results:
            context += "\n\nAdditional Context:\n"
            for idx, result in enumerate(search_results[:3], 1):
                content = result.get('content', '') if isinstance(result, dict) else str(result)
                context += f"{idx}. {content}\n"
        
        # Step 4: Generate interpretation
        yield "💡 **Interpretation:**\n\n"
        
        interpretation_prompt = f"""Based on the SQL query results below, provide a clear and concise interpretation of the data to answer the user's question.

User Question: {prompt}

SQL Query:
{generated_sql}

{context}

Provide a natural language summary of the results, highlighting key insights and answering the user's question directly."""
        
        escaped_prompt = interpretation_prompt.replace("'", "''")
        
        cursor = st.session_state.CONN.cursor(DictCursor)
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA}")
        
        sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large2',
            '{escaped_prompt}'
        ) as response
        """
        
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        
        if result and 'RESPONSE' in result:
            response_text = result['RESPONSE']
            
            if isinstance(response_text, str):
                # Yield the response in chunks for streaming effect
                words = response_text.split()
                for i in range(0, len(words), 5):
                    chunk = ' '.join(words[i:i+5]) + ' '
                    yield chunk
            else:
                yield str(response_text)
        else:
            yield "No interpretation available."
            
    except Exception as e:
        yield f"\n\n❌ Error: {str(e)}"

def main():

    with st.sidebar:
        st.write(f"**Database:** {DATABASE}")
        st.write(f"**Schema:** {SCHEMA}")
        st.write(f"**Warehouse:** {WAREHOUSE}")
        
        # Show available tables
        if 'CONN' in st.session_state and st.session_state.CONN is not None:
            tables = get_available_tables()
            if tables:
                st.write("**Available Tables:**")
                for table in tables:
                    st.write(f"- {table}")
        
        if st.button("Reset Conversation", key="new_chat"):
            st.session_state.messages = []
            st.rerun()

    st.title("Intelligent Sales Assistant")

    # connection
    if 'CONN' not in st.session_state or st.session_state.CONN is None:

        try: 
            st.session_state.CONN = snowflake.connector.connect(
                user=USER,
                password=PASSWORD,
                account=ACCOUNT,
                host=HOST,
                port=443,
                role=ROLE,
                warehouse=WAREHOUSE,
                database=DATABASE,
                schema=SCHEMA
            )  
            st.success('Snowflake Connection established!', icon="✅")    
        except Exception as e:
            st.error(f'Connection not established. Error: {str(e)}', icon="🚨")
            return

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'].replace("•", "\n\n-"))

    # Handle user input
    if user_input := st.chat_input("What is your question?"):

        # Add user message to chat       
        with st.chat_message("user"):
            st.markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

        # Get response from Cortex Agent
        with st.chat_message("assistant"):
            response_generator = agent_api_call(user_input, "session_1")
            text = st.write_stream(response_generator)

            # Add assistant response to chat
            if text:
                st.session_state.messages.append({"role": "assistant", "content": text})

      
if __name__ == "__main__":
    main()