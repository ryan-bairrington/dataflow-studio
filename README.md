# DataFlow Studio 🔄

[![CI](https://github.com/YOUR_USERNAME/dataflow-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/dataflow-studio/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)

A visual data workflow builder inspired by Alteryx. Build data transformation pipelines using drag-and-drop nodes, execute them, and export results — no coding required!

![DataFlow Studio Screenshot](docs/screenshot.png)

## ✨ Features

- **🎨 Visual Canvas**: Drag-and-drop nodes to build workflows
- **🧩 8 Node Types**: ReadCSV, Filter, Select, Join, Aggregate, Sort, Formula, Output
- **👁️ Real-time Preview**: Click any node to see its output
- **📥 Export**: Download your transformed data as CSV
- **🔒 Safe Expressions**: Sandboxed expression evaluation for filters and formulas
- **🚀 Fast Execution**: Pandas-powered data processing

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐
│ React Frontend  │◄───►│ FastAPI Backend  │
│ (react-flow)    │ REST │ (Python/Pandas) │
└─────────────────┘     └────────┬────────┘
                                 │
                      ┌─────────┴─────────┐
                      │ Workflow Executor │
                      │ (Topological Sort)│
                      └─────────┬─────────┘
                                │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
  ┌──────┴──────┐  ┌─────┴───────┐ ┌─────┴────────┐
  │  I/O Nodes   │  │ Transform   │ │ Combine      │
  │ (Read, Out)  │  │ (Filter...) │ │ (Join, Agg)  │
  └─────────────┘  └─────────────┘ └──────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Backend Setup

```bash
cd backend
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser. 🎉

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload a CSV file |
| `POST` | `/api/run-workflow` | Execute a workflow |
| `GET` | `/api/download/{id}` | Download result CSV |
| `GET` | `/api/nodes` | List available node types |

<details>
<summary>📝 API Examples</summary>

### Upload a file
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@mydata.csv"
```

### Run a workflow
```bash
curl -X POST http://localhost:8000/api/run-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": {
      "nodes": [
        {"id": "n1", "type": "ReadCSV", "config": {"upload_id": "..."}},
        {"id": "n2", "type": "Filter", "config": {"expression": "age > 18"}}
      ],
      "edges": [
        {"fromNodeId": "n1", "toNodeId": "n2"}
      ]
    }
  }'
```
</details>

## 🧩 Available Nodes

| Node | Category | Description | Key Config |
|------|----------|-------------|------------|
| **ReadCSV** | 🟢 Input | Load CSV files | `upload_id`, `header`, `sep` |
| **Filter** | 🟦 Transform | Filter rows | `expression` |
| **Select** | 🟦 Transform | Choose columns | `columns` |
| **Sort** | 🟦 Transform | Sort rows | `columns`, `ascending` |
| **Formula** | 🟣 Transform | Calculate new column | `newCol`, `expression` |
| **Join** | 🟠 Combine | Join two datasets | `leftKey`, `rightKey`, `how` |
| **Aggregate** | 🟠 Combine | Group and summarize | `groupBy`, `aggregations` |
| **Output** | 🔴 Output | Export results | `format` |

## 🔐 Security

### Expression Sandboxing

The `SafeExpressionParser` provides secure expression evaluation:

- ✅ Blocks `exec()`, `eval()`, `import`, `__dunder__` access
- ✅ Uses `pandas.eval()` with restricted namespace  
- ✅ Whitelisted functions only (math, string operations)
- ✅ AST validation before execution

### MVP Limitations

- ⚠️ No user authentication (single-user mode)
- ⚠️ Files stored temporarily (not persistent)
- ⚠️ Expression syntax limited to Pandas-compatible operations

## 🧪 Testing

```bash
# Backend
cd backend
pytest -v                          # Run tests
pytest --cov=app --cov-report=html # With coverage

# Frontend  
cd frontend
npm test                           # Run tests
```

## 📖 Documentation

- [Developer Guide](docs/DEVELOPER.md) - How to add new nodes, architecture details
- [API Specification](docs/API.md) - Detailed API documentation
- [Contributing](CONTRIBUTING.md) - How to contribute

## 📁 Project Structure

```
dataflow-studio/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── main.py          # Entry point
│   │   ├── routes.py        # API endpoints
│   │   ├── models.py        # Pydantic models
│   │   └── engine/          # Execution engine
│   │       ├── executor.py  # Workflow orchestration
│   │       ├── parser.py    # Expression parser
│   │       └── nodes/       # Node implementations
│   └── tests/               # pytest tests
├── frontend/                # React + TypeScript
│   └── src/
│       ├── components/      # React components
│       ├── hooks/           # Custom hooks
│       ├── config/          # Node definitions
│       └── api/             # API client
├── examples/                # Sample data & workflows
└── docs/                    # Documentation
```

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📜 License

[MIT License](LICENSE) - Build cool stuff!

---

<p align="center">
  Made with ❤️ and 🐼 pandas
</p>
