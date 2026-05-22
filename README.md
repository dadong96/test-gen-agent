# Test Gen Agent

AI-driven multi-agent system for automated JUnit 5 test generation from PRD documents, Swagger/OpenAPI specs, and Java source code AST, with a coverage-based feedback loop.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                              CLI / CI                                │
│                   (python -m src.cli generate ./project)             │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │     Orchestrator       │
                    │  Coordinates 4-agent   │
                    │  pipeline with retry   │
                    └───┬────┬────┬────┬────┘
                        │    │    │    │
         ┌──────────────▼┐ ┌▼────▼┐ ┌▼────────────┐
         │  Parser Agent │ │Generator│ │Optimizer  │
         │               │ │ Agent  │ │  Agent     │
         │ · PRD parsing │ │ · AST  │ │ · Dedup    │
         │ · Swagger     │ │ · Gen  │ │ · Merge    │
         │ · Rules       │ │ · JUnit│ │ · Priority │
         └───────────────┘ └───────┘ └────────────┘
                                       │
                              ┌────────▼────────┐
                              │  Runner Agent    │
                              │ · mvn/gradle     │
                              │ · JaCoCo report  │
                              │ · Uncovered →    │
                              │   back to Gen    │
                              └─────────────────┘
```

### 4-Agent Pipeline

| Stage | Agent | Role | Output |
|-------|-------|------|--------|
| 1 | **Parser** | Extract business rules from PRD + Swagger | `RequirementSpec` |
| 2 | **Generator** | Generate JUnit 5 tests from spec + AST | `TestCase[]` |
| 3 | **Optimizer** | Deduplicate, merge, prioritize tests | Optimized `TestCase[]` |
| 4 | **Runner** | Execute tests, parse JaCoCo coverage | Coverage reports + retry signal |

### Coverage Feedback Loop

When branch coverage falls below the threshold, the Runner feeds uncovered branches back to the Generator for supplementary test generation. This loop runs up to 3 rounds with increasing thresholds.

## Quick Start

### 1. Install

```bash
git clone https://github.com/dadong96/test-gen-agent.git
cd test-gen-agent
pip install -e ".[dev]"
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY or OPENAI_API_KEY
```

### 3. Generate Tests

```bash
# Full pipeline: parse docs → generate tests → run → coverage loop
python -m src.cli generate \
  --project ./examples/sample_project \
  --prd ./examples/sample_prd.md \
  --swagger ./examples/sample_swagger.json

# Parse docs only (dry run)
python -m src.cli generate \
  --project ./my-java-project \
  --prd ./docs/prd.md \
  --dry-run

# Generate without executing tests
python -m src.cli generate \
  --project ./my-java-project \
  --prd ./docs/prd.md \
  --swagger ./docs/swagger.json \
  --no-run

# Custom coverage threshold and retry rounds
python -m src.cli generate \
  --project ./my-java-project \
  --prd ./docs/prd.md \
  --swagger ./docs/swagger.json \
  --coverage-threshold 0.8 \
  --max-rounds 3
```

## CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--project` | (required) | Path to the Java project |
| `--prd` | (required) | Path to the PRD document (Markdown) |
| `--swagger` | None | Path to the Swagger/OpenAPI spec (JSON) |
| `--coverage-threshold` | 0.70 | Target branch coverage threshold |
| `--max-rounds` | 3 | Maximum coverage retry rounds |
| `--no-run` | false | Generate tests but skip execution |
| `--dry-run` | false | Parse docs only, no test generation |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Anthropic API key for Claude |
| `ANTHROPIC_MODEL` | claude-sonnet-4-6-20250514 | Claude model to use |
| `OPENAI_API_KEY` | — | OpenAI API key (fallback) |
| `OPENAI_BASE_URL` | https://api.openai.com/v1 | OpenAI-compatible endpoint |
| `COVERAGE_THRESHOLD_DEFAULT` | 0.70 | Default branch coverage target |
| `COVERAGE_THRESHOLD_INCREMENT` | 0.10 | Threshold increase per retry round |
| `MAX_COVERAGE_ROUNDS` | 3 | Maximum coverage feedback loops |
| `MAX_FILES_PER_RUN` | 50 | Max Java files to process per run |

## Project Structure

```
test-gen-agent/
├── config/
│   └── settings.py              # Global configuration
├── src/
│   ├── main.py                  # Programmatic entry point
│   ├── cli.py                   # CLI interface
│   ├── agents/
│   │   ├── base.py              # Base agent class
│   │   ├── parser_agent.py      # PRD + Swagger parsing
│   │   ├── generator_agent.py   # Test case generation
│   │   ├── optimizer_agent.py   # Dedup + prioritization
│   │   └── runner_agent.py      # Test execution + coverage
│   ├── core/
│   │   ├── orchestrator.py      # Pipeline coordinator
│   │   ├── llm_client.py        # LLM API client
│   │   ├── ast_parser.py        # Java AST (tree-sitter)
│   │   ├── coverage_parser.py   # JaCoCo CSV parser
│   │   ├── build_executor.py    # Maven/Gradle runner
│   │   └── types.py             # Shared data types
│   ├── generators/
│   │   └── junit_writer.py      # JUnit 5 file writer
│   └── utils/
│       ├── file_utils.py        # File helpers
│       └── logger.py            # Logging setup
├── templates/
│   └── junit5_template.java     # JUnit 5 Jinja2 template
├── tests/                       # Test suite
├── examples/
│   ├── sample_prd.md            # Example PRD
│   ├── sample_swagger.json      # Example OpenAPI spec
│   └── sample_project/          # Example Java project
└── pyproject.toml
```

## Programmatic Usage

```python
from src.main import run_test_generation
import asyncio

async def main():
    result = await run_test_generation(
        project_path="./my-java-project",
        prd_path="./docs/prd.md",
        swagger_path="./docs/swagger.json",
        coverage_threshold=0.8,
    )
    print(f"Generated {len(result.generated_tests)} tests")
    print(f"Status: {result.status}")

asyncio.run(main())
```

## Tech Stack

| Component | Choice | Purpose |
|-----------|--------|---------|
| Agent Orchestration | Python asyncio | Multi-agent pipeline |
| LLM | Anthropic Claude / OpenAI | Test generation + analysis |
| Java AST | tree-sitter-java | Source code parsing |
| Test Execution | Maven/Gradle subprocess | Running generated tests |
| Coverage | JaCoCo CSV parsing | Coverage feedback loop |
| Template Engine | Jinja2 | JUnit 5 file generation |

## License

MIT
