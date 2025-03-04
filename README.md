# PostgreSQL AI Agent

  

A conversational AI agent for PostgreSQL databases, inspired by Pandas AI. This agent allows users to interact with their PostgreSQL database using natural language, without needing to write SQL queries.

  

## Features

  

- **Natural Language to SQL:** Converts natural language questions into SQL queries

- **Data Visualization:** Generates charts and graphs from query results

- **Query Routing:** Intelligently routes queries to specialized handlers

- **User-Friendly Interface:** Simple chat interface for interacting with your data

- **PostgreSQL Integration:** Works directly with your PostgreSQL database
  

## Architecture

  

The system consists of the following main components:

  

1. **Central Query Router:** Analyzes user queries and routes them to specialized agents

2. **Text2SQL Agent:** Converts natural language to SQL

3. **Visualization Agent:** Creates visual representations of data

4. **Chat Agent:** Handles general conversational queries

5. **PostgreSQL Connector:** Securely executes queries against the database


  

## Getting Started

  

### Prerequisites

  

- Python 3.8+

- PostgreSQL database

- OpenAI API key (or another LLM provider)

  

### Installation

  

1. Clone this repository
```bash
git clone https://github.com/aspisov/database-agent.git
cd database-agent
```

2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

  

3. Install dependencies
```bash
pip install -r requirements.txt
```

  

1. Set up your environment variables by creating a `.env` file:

```
# Database settings

DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password

# OpenAI settings
OPENAI_API_KEY=your_openai_api_key
LLM_MODEL=gpt-4o-mini
```

  

### Running the Application

  

Start the application with:


```bash
python -m src.main
```

The Streamlit UI will open in your default web browser.

  

### Using Docker

  

You can also run the application using Docker:

```bash
docker-compose up -d
```

This will start both the application and a PostgreSQL database.

## Project Structure

```
database-agent/
├── .env # Environment variables
├── .gitignore # Git ignore file
├── Dockerfile # For containerizing the application
├── docker-compose.yml # For local development with PostgreSQL
├── README.md # Project documentation
├── requirements.txt # Python dependencies
├── setup.py # For packaging the application
├── tests/ # Test directory
│ ├── __init__.py
│ ├── conftest.py # Pytest fixtures
│ ├── test_agents/ # Tests for agents
│ ├── test_database/ # Tests for database connections
│ └── test_ui/ # Tests for UI components
├── config/ # Configuration
│ ├── __init__.py
│ ├── settings.py # Application settings
│ └── logging_config.py # Logging configuration
└── src/ # Source code
├── __init__.py
├── main.py # Application entry point
├── agents/ # Agent modules
│ ├── __init__.py
│ ├── router.py # Query router agent
│ ├── text2sql.py # Text2SQL agent
│ ├── visualization.py # Visualization agent
│ └── chat.py # Chat agent
├── database/ # Database operations
│ ├── __init__.py
│ ├── connector.py # Database connector
│ └── models.py # Database models/schema
├── ui/ # User interface
│ ├── __init__.py
│ ├── app.py # Streamlit app
│ ├── components/ # UI components
│ └── pages/ # UI pages
└── utils/ # Utility functions
├── __init__.py
├── error_handling.py # Error handling utilities
├── logging.py # Logging utilities
└── security.py # Security utilities
```

  

## Development

  

### Adding New Features
1. For new agent types, create a new file in the `src/agents/` directory
2. For UI enhancements, modify files in the `src/ui/` directory
3. For database improvements, modify files in the `src/database/` directory

## License

MIT

  

## Acknowledgments

  

- Inspired by [Pandas AI](https://github.com/gventuri/pandas-ai)

- Uses [OpenAI](https://openai.com/) for natural language processing

- Built with [Streamlit](https://streamlit.io/) for the UI