from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import create_engine, inspect, text

import os
from dotenv import load_dotenv

from urllib.parse import quote

import re

load_dotenv()

apiKey = os.getenv('GOOGLE_API_KEY')

# Initialize Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=apiKey)
print("bye")
print(llm)

# Invoke the model
result = llm.invoke("What is the square root of 36?")

# Print result
print(result)

# Function to connect to MySQL dynamically
def connect_to_db(db_type, host, port, dbname, user, password):
    try:
        # Use the correct database URL format
        DATABASE_URL = f"{db_type}+pymysql://{user}:{quote(password)}@{host}:{port}/{dbname}"
        engine = create_engine(DATABASE_URL)

        # Test the connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))  # Simple test query
        print("✅ Database connection successful!")
        return engine
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

# Function to retrieve table and column details
def get_schema_info(engine):
    if engine is None:
        print("❌ Database connection failed. Cannot retrieve schema.")
        return None

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        schema_info = {}
        for table in tables:
            schema_info[table] = [column["name"] for column in inspector.get_columns(table)]
        
        return schema_info
    except Exception as e:
        print(f"❌ Error retrieving schema: {e}")
        return None


# Function to execute the generated SQL query
def execute_query(engine, query):
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            rows = result.fetchall()
            return rows
    except Exception as e:
        print(f"❌ Error executing SQL query: {e}")
        return None
    

# Get user database details
db_engine = connect_to_db(
    db_type=os.getenv('db_type'),  # Make sure the database type is correct
    host=os.getenv('host'),
    port=os.getenv('port'),
    dbname=os.getenv('dbname'),
    user=os.getenv('user'),
    password=os.getenv('password')
)

# Fetch schema information
schema_info = get_schema_info(db_engine)
if schema_info:
    # print("📊 Database Schema:", schema_info)


      # User's natural language question
    user_question = "list names of all the students, use sql join"
    

    # Format the schema info into the prompt
    prompt = f"""
    Database Schema: {schema_info}
    User Question: "{user_question}"
    Generate an optimized SQL query that works with this schema.
    """

    # Invoke Gemini to generate SQL
    result = llm.invoke(prompt)

    # Extract only the SQL query by removing extra explanations
    cleaned_sql = re.search(r"SELECT.*?;", result.content, re.DOTALL)

    if cleaned_sql:
        generated_query = cleaned_sql.group(0).strip()
    else:
        generated_query = result.content.strip()  # Fallback in case regex fails

    print("\n📝 Final Cleaned SQL Query:\n", generated_query)


    # Execute the generated query in the database
    query_result = execute_query(db_engine, generated_query)
    print(query_result)