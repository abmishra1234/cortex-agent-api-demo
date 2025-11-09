import json
import requests
import streamlit as st
import snowflake.connector  # type: ignore
from snowflake.connector import DictCursor  # type: ignore

from logger import logger, log_call  # NEW IMPORT

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

@log_call
def get_available_tables():
    """Get list of available tables in the schema"""
    try:
        cursor = st.session_state.CONN.cursor(DictCursor)
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA}")
        sql = "SHOW TABLES"
        logger.debug(f"Executing SQL (list tables): {sql}")
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        tables = [row['name'] for row in results]
        logger.info(f"Retrieved tables: {tables}")
        return tables
    except Exception as e:
        logger.exception(f"get_available_tables failed: {e}")
        st.error(f"Could not get tables: {str(e)}")
        return []

@log_call
def run_snowflake_query(query):
    """Execute a Snowflake query safely (semicolon stripped)."""
    try:
        sanitized = query.replace(';', '')
        logger.debug(f"Original query: {query}")
        logger.debug(f"Sanitized query: {sanitized}")
        cursor = st.session_state.CONN.cursor(DictCursor)
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA}")
        cursor.execute(sanitized)
        results = cursor.fetchall()
        cursor.close()
        logger.info(f"Query returned rows={len(results)}")
        return results
    except Exception as e:
        logger.exception(f"run_snowflake_query error: {e}")
        st.error(f"Error executing SQL: {str(e)}")
        return None

@log_call
def get_cortex_search_context(query: str):
    """Get relevant context from Cortex Search Service (handles versioned signatures)."""
    try:
        cursor = st.session_state.CONN.cursor(DictCursor)
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA}")

        escaped_query = query.replace("'", "''")
        payload = f"OBJECT_CONSTRUCT('query', '{escaped_query}', 'limit', 5)"

        sql_two = f"""
        SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            '{CORTEX_SEARCH_SERVICES}',
            {payload}
        ) AS search_results
        """
        sql_three = f"""
        SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            '{CORTEX_SEARCH_SERVICES}',
            '{escaped_query}',
            OBJECT_CONSTRUCT('limit', 5)
        ) AS search_results
        """

        signature = "two-arg-object"
        try:
            logger.debug("Trying SEARCH_PREVIEW (service, OBJECT payload)")
            cursor.execute(sql_two)
        except Exception as e2:
            logger.warning(f"SEARCH_PREVIEW(2) not supported: {e2}")
            logger.debug("Trying SEARCH_PREVIEW legacy (service, query, options)")
            cursor.execute(sql_three)
            signature = "three-arg"
        row = cursor.fetchone()
        cursor.close()
        logger.debug(f"SEARCH_PREVIEW signature={signature} row={row}")

        if not row or 'SEARCH_RESULTS' not in row:
            logger.info("Search returned no data")
            return []

        data = row['SEARCH_RESULTS']
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                logger.warning("Search results not JSON; returning empty")
                return []

        if isinstance(data, dict):
            items = data.get('results') or data.get('data') or []
        elif isinstance(data, list):
            items = data
        else:
            items = []

        if not isinstance(items, list):
            items = []

        limited = items[:5]
        logger.info(f"Search items total={len(items)} returned={len(limited)} signature={signature}")
        return limited
    except Exception as e:
        logger.exception(f"get_cortex_search_context failure: {e}")
        st.warning(f"Could not retrieve search context: {str(e)}")
        return []

@log_call
def generate_sql_from_question(user_query: str, tables: list):
    """Use Cortex to generate SQL from natural language question"""
    try:
        cursor = st.session_state.CONN.cursor(DictCursor)
        cursor.execute(f"USE DATABASE {DATABASE}")
        cursor.execute(f"USE SCHEMA {SCHEMA}")

        table_schemas = {}
        for table in tables:
            logger.debug(f"Describing table: {table}")
            cursor.execute(f"DESCRIBE TABLE {table}")
            columns = cursor.fetchall()
            table_schemas[table] = [{"name": col["name"], "type": col["type"]} for col in columns]

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
        logger.debug(f"Generation prompt length={len(escaped_prompt)}")

        sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large2',
            '{escaped_prompt}'
        ) as sql_query
        """
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        logger.debug(f"Raw generate_sql result row: {result}")

        if result and 'SQL_QUERY' in result:
            generated_sql = result['SQL_QUERY'].strip()
            cleaned = generated_sql.replace('```sql', '').replace('```', '').strip()
            logger.info(f"Generated SQL length={len(cleaned)}")
            return cleaned
        logger.warning("No SQL generated")
        return None
    except Exception as e:
        logger.exception(f"generate_sql_from_question error: {e}")
        st.error(f"Error generating SQL: {str(e)}")
        return None

@log_call
def agent_api_call(prompt: str, session_id: str):
    """Generator orchestrating end-to-end workflow."""
    try:
        logger.info(f"Agent started session_id={session_id} prompt_len={len(prompt)}")
        tables = get_available_tables()

        if not tables:
            msg = "No tables found in the database. Please check your database configuration."
            logger.warning(msg)
            yield msg
            return

        yield "🔍 Analyzing your question...\n\n"
        generated_sql = generate_sql_from_question(prompt, tables)

        if not generated_sql:
            logger.warning("SQL generation failed")
            yield "❌ Could not generate SQL query from your question."
            return

        yield f"📝 **Generated SQL Query:**\n```sql\n{generated_sql}\n```\n\n"
        yield "⚙️ Executing query...\n\n"
        query_results = run_snowflake_query(generated_sql)

        if query_results is None:
            logger.error("Query execution returned None (error)")
            yield "❌ Error executing the query."
            return

        if not query_results:
            yield "📊 **Query Results:** No data found.\n\n"
            result_context = "No results returned from the query."
            logger.info("Empty result set")
        else:
            yield f"📊 **Query Results:** Found {len(query_results)} rows.\n\n"
            logger.info(f"Result rows count={len(query_results)}")
            result_context = "Query Results:\n"
            for idx, row in enumerate(query_results[:10], 1):
                row_json = json.dumps(dict(row), default=str)
                result_context += f"{idx}. {row_json}\n"

        search_results = get_cortex_search_context(prompt)
        context = result_context
        if search_results:
            logger.info(f"Search context count={len(search_results)}")
            context += "\n\nAdditional Context:\n"
            for idx, result in enumerate(search_results[:3], 1):
                content = result.get('content', '') if isinstance(result, dict) else str(result)
                context += f"{idx}. {content}\n"
        else:
            logger.info("No additional search context")

        yield "💡 **Interpretation:**\n\n"
        interpretation_prompt = f"""Based on the SQL query results below, provide a clear and concise interpretation of the data to answer the user's question.

User Question: {prompt}

SQL Query:
{generated_sql}

{context}

Provide a natural language summary of the results, highlighting key insights and answering the user's question directly."""
        escaped_prompt = interpretation_prompt.replace("'", "''")
        logger.debug(f"Interpretation prompt length={len(escaped_prompt)}")

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
        logger.debug(f"Interpretation raw row: {result}")

        if result and 'RESPONSE' in result:
            response_text = result['RESPONSE']
            logger.info(f"Interpretation response_type={type(response_text).__name__}")
            if isinstance(response_text, str):
                words = response_text.split()
                for i in range(0, len(words), 5):
                    chunk = ' '.join(words[i:i+5]) + ' '
                    yield chunk
            else:
                yield str(response_text)
        else:
            logger.warning("No interpretation available")
            yield "No interpretation available."
    except Exception as e:
        logger.exception(f"agent_api_call fatal error: {e}")
        yield f"\n\n❌ Error: {str(e)}"

@log_call
def main():
    logger.info("Application start main()")
    with st.sidebar:
        st.write(f"**Database:** {DATABASE}")
        st.write(f"**Schema:** {SCHEMA}")
        st.write(f"**Warehouse:** {WAREHOUSE}")

        if 'CONN' in st.session_state and st.session_state.CONN is not None:
            tables = get_available_tables()
            if tables:
                st.write("**Available Tables:**")
                for table in tables:
                    st.write(f"- {table}")
            else:
                logger.warning("Sidebar: no tables to list")

        if st.button("Reset Conversation", key="new_chat"):
            logger.info("Conversation reset triggered")
            st.session_state.messages = []
            st.rerun()

    st.title("Intelligent Sales Assistant")

    if 'CONN' not in st.session_state or st.session_state.CONN is None:
        try:
            logger.info("Establishing Snowflake connection...")
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
            logger.info("Snowflake connection established")
        except Exception as e:
            logger.exception(f"Connection failed: {e}")
            st.error(f'Connection not established. Error: {str(e)}', icon="🚨")
            return

    if 'messages' not in st.session_state:
        st.session_state.messages = []
        logger.debug("Initialized messages list")

    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'].replace("•", "\n\n-"))

    if user_input := st.chat_input("What is your question?"):
        logger.info(f"User input received len={len(user_input)}")
        with st.chat_message("user"):
            st.markdown(user_input)
            st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            response_generator = agent_api_call(user_input, "session_1")
            text = st.write_stream(response_generator)
            if text:
                st.session_state.messages.append({"role": "assistant", "content": text})
                logger.info("Assistant response appended to history")

if __name__ == "__main__":
    main()