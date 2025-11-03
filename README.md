# Semche

MCP Server for vector search functionality.

## Overview

This project provides a Model Context Protocol (MCP) server that will eventually support vector search capabilities using LangChain and ChromaDB. Currently, it implements a simple skeleton with a `hello` tool for testing and validation.

## Features

- **MCP Server**: Implements the Model Context Protocol
- **Hello Tool**: Simple greeting tool for testing (returns "Hello, {name}!")

## Requirements

- Python 3.10 or higher
- uv (for package management)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/paterapatera/semche.git
cd semche
```

2. Install dependencies using uv:

```bash
uv sync
```

3. Install development dependencies (includes MCP Inspector):

```bash
uv sync --extra dev
```

## Usage

### Running the MCP Server

Run the server using uv:

```bash
uv run python src/semche/mcp_server.py
```

The server will start and listen on stdio for MCP protocol messages.

### Testing with MCP Inspector

You can test the server using MCP Inspector:

```bash
uv run mcp dev src/semche/mcp_server.py
```

This will start an interactive inspector where you can:

1. View available tools
2. Call the `hello` tool with different parameters
3. Inspect the responses

Example usage in MCP Inspector:

- Call `hello` without parameters: Returns "Hello, World!"
- Call `hello` with name "Alice": Returns "Hello, Alice!"

### Running Tests

Run the test suite using pytest:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=semche --cov-report=html
```

## Project Structure

```
/home/pater/semche/
├── src/
│   └── semche/
│       ├── __init__.py
│       └── mcp_server.py      # MCP server implementation
├── tests/
│   ├── __init__.py
│   └── test_mcp_server.py     # Tests for MCP server
├── pyproject.toml             # Project configuration
├── README.md                  # This file
└── .gitignore                 # Git ignore patterns
```

## Available Tools

### hello

Returns a greeting message.

**Parameters:**

- `name` (string, optional): Name to greet. Defaults to "World".

**Returns:**

- Greeting message in the format "Hello, {name}!"

**Example:**

```json
{
  "name": "hello",
  "arguments": {
    "name": "Alice"
  }
}
```

**Response:**

```
Hello, Alice!
```

## Development

### Adding New Tools

To add a new tool:

1. Add the tool definition in the `list_tools()` function
2. Implement the tool logic in the `call_tool()` function
3. Add tests in `tests/test_mcp_server.py`

### Future Enhancements

- Vector embedding generation using LangChain
- ChromaDB integration for vector storage
- Similarity search functionality
- Batch processing capabilities

## License

TBD

## Contributing

TBD
