import pytest
from unittest.mock import patch, MagicMock
from app.agent.sql_agent import get_sql_agent


@patch('app.agent.sql_agent.create_sql_agent', return_value=MagicMock())
@patch('app.agent.sql_agent.SQLDatabaseToolkit', return_value=MagicMock())
@patch('app.agent.sql_agent.OpenAI', return_value=MagicMock())
@patch('app.agent.sql_agent.SQLDatabase', return_value=MagicMock())
def test_get_sql_agent_initialization(_, __, ___, ____):
    """get_sql_agent should initialise without raising import/type errors."""
    try:
        get_sql_agent()
    except (ImportError, TypeError, ValueError) as e:
        pytest.fail(f"Agent initialization failed unexpectedly: {e}") 