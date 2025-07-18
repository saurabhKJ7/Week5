import logging
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import OpenAI
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent

from app.core.config import settings

PROMPT_PREFIX = """
You are a PostgreSQL expert. Given an input question, first create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples to obtain, query for at most 5 results using the LIMIT clause.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.

You have access to a table called `v_current_prices` which contains the most up-to-date price information. 
This view has the following columns: `product_name`, `platform_name`, `price`, `currency`, `product_description`, `category_name`, `brand_name`.
ALWAYS use the `v_current_prices` view when the user asks about prices, products, or platforms. Do NOT query the individual tables.

For questions about cheapest products, ALWAYS:
1. Use ORDER BY price ASC LIMIT 1 in your query
2. Format your response EXACTLY like this example, replacing the values with actual data from your query:
   "Walmart has the cheapest bananas at 0.99 USD."

Example question: "Which store has the cheapest bananas?"
Example query: 
SELECT platform_name, product_name, price, currency 
FROM v_current_prices 
WHERE product_name ILIKE '%banana%' 
ORDER BY price ASC LIMIT 1;

Example response: "Walmart has the cheapest bananas at 0.99 USD."

DO NOT use placeholders or brackets in your response. Always use actual values from your query results.
If no results are found, respond with: "Sorry, I couldn't find any matching products in the database."
"""

def get_sql_agent():
    """Initialise and return a LangChain SQL agent."""
    db = SQLDatabase.from_uri(settings.SYNC_DATABASE_URL)
    llm = OpenAI(temperature=0)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=True,
        prefix=PROMPT_PREFIX,
    )
    return agent_executor 