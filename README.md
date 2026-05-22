# Test Gen Agent

基于多 Agent 协作的端到端测试用例自动生成系统。从 PRD 需求文档 + Swagger 接口文档 + Java 源码 AST 自动生成 JUnit 5 测试用例，并通过覆盖率闭环持续补充未覆盖分支。

## 系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                           CLI / CI 入口                              │
│                (python -m src.cli generate ./project)                │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │     Orchestrator       │
                    │   协调 4 Agent 流水线   │
                    │   管理覆盖率闭环重试    │
                    └───┬────┬────┬────┬────┘
                        │    │    │    │
         ┌──────────────▼┐ ┌▼────▼┐ ┌▼────────────┐
         │  Parser Agent │ │Generator│ │Optimizer  │
         │               │ │ Agent  │ │  Agent     │
         │ · PRD 解析    │ │ · AST  │ │ · 去重     │
         │ · Swagger 解析│ │ · 生成 │ │ · 合并     │
         │ · 业务规则提取│ │ · JUnit│ │ · 优先级   │
         └───────────────┘ └───────┘ └────────────┘
                                       │
                              ┌────────▼────────┐
                              │  Runner Agent    │
                              │ · mvn/gradle 执行│
                              │ · JaCoCo 覆盖率  │
                              │ · 未覆盖 →       │
                              │   回传 Generator │
                              └─────────────────┘
```

### 四 Agent 流水线

| 阶段 | Agent | 职责 | 输出 |
|------|-------|------|------|
| 1 | **Parser** | 从 PRD + Swagger 提取业务规则和接口定义 | `RequirementSpec` |
| 2 | **Generator** | 结合 AST + 需求规格生成 JUnit 5 测试用例 | `TestCase[]` |
| 3 | **Optimizer** | 去重、合并相似用例、标注优先级 | 优化后的 `TestCase[]` |
| 4 | **Runner** | 执行测试、解析 JaCoCo 覆盖率报告 | 覆盖率报告 + 重试信号 |

### 覆盖率闭环

当分支覆盖率低于阈值时，Runner 将未覆盖的分支信息回传给 Generator，触发补充生成。最多重试 3 轮，每轮递增覆盖率阈值。

## 快速开始

### 1. 安装

```bash
git clone https://github.com/dadong96/test-gen-agent.git
cd test-gen-agent
pip install -e ".[dev]"
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY 或 OPENAI_API_KEY
```

### 3. 生成测试用例

```bash
# 完整流水线：解析文档 → 生成测试 → 执行 → 覆盖率闭环
python -m src.cli generate \
  --project ./examples/sample_project \
  --prd ./examples/sample_prd.md \
  --swagger ./examples/sample_swagger.json

# 仅解析文档（dry run）
python -m src.cli generate \
  --project ./my-java-project \
  --prd ./docs/prd.md \
  --dry-run

# 生成测试但不执行
python -m src.cli generate \
  --project ./my-java-project \
  --prd ./docs/prd.md \
  --swagger ./docs/swagger.json \
  --no-run

# 自定义覆盖率阈值和重试轮数
python -m src.cli generate \
  --project ./my-java-project \
  --prd ./docs/prd.md \
  --swagger ./docs/swagger.json \
  --coverage-threshold 0.8 \
  --max-rounds 3
```

## CLI 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--project` | （必填） | Java 项目路径 |
| `--prd` | （必填） | PRD 需求文档路径（Markdown） |
| `--swagger` | 无 | Swagger/OpenAPI 接口文档路径（JSON） |
| `--coverage-threshold` | 0.70 | 目标分支覆盖率阈值 |
| `--max-rounds` | 3 | 最大覆盖率重试轮数 |
| `--no-run` | false | 仅生成测试，不执行 |
| `--dry-run` | false | 仅解析文档，不生成测试 |

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ANTHROPIC_API_KEY` | — | Anthropic API Key（Claude） |
| `ANTHROPIC_MODEL` | claude-sonnet-4-6-20250514 | 使用的 Claude 模型 |
| `OPENAI_API_KEY` | — | OpenAI API Key（备选） |
| `OPENAI_BASE_URL` | https://api.openai.com/v1 | OpenAI 兼容接口地址 |
| `COVERAGE_THRESHOLD_DEFAULT` | 0.70 | 默认分支覆盖率目标 |
| `COVERAGE_THRESHOLD_INCREMENT` | 0.10 | 每轮重试递增的阈值 |
| `MAX_COVERAGE_ROUNDS` | 3 | 最大覆盖率闭环轮数 |
| `MAX_FILES_PER_RUN` | 50 | 单次最多处理的 Java 文件数 |

## 项目结构

```
test-gen-agent/
├── config/
│   └── settings.py              # 全局配置
├── src/
│   ├── main.py                  # 编程入口
│   ├── cli.py                   # CLI 命令行
│   ├── agents/
│   │   ├── base.py              # Agent 基类
│   │   ├── parser_agent.py      # PRD + Swagger 文档解析
│   │   ├── generator_agent.py   # 测试用例生成
│   │   ├── optimizer_agent.py   # 去重 + 优先级排序
│   │   └── runner_agent.py      # 测试执行 + 覆盖率解析
│   ├── core/
│   │   ├── orchestrator.py      # 流水线协调器（含闭环逻辑）
│   │   ├── llm_client.py        # LLM API 客户端
│   │   ├── ast_parser.py        # Java AST 解析（tree-sitter）
│   │   ├── coverage_parser.py   # JaCoCo CSV 覆盖率解析
│   │   ├── build_executor.py    # Maven/Gradle 构建执行
│   │   └── types.py             # 共享数据结构
│   ├── generators/
│   │   └── junit_writer.py      # JUnit 5 文件生成器（Jinja2）
│   └── utils/
│       ├── file_utils.py        # 文件工具函数
│       └── logger.py            # 日志配置
├── templates/
│   └── junit5_template.java     # JUnit 5 测试文件模板
├── tests/                       # 测试套件
├── examples/
│   ├── sample_prd.md            # 示例 PRD 文档
│   ├── sample_swagger.json      # 示例 OpenAPI 接口文档
│   └── sample_project/          # 示例 Java 项目（OrderService）
└── pyproject.toml
```

## 编程方式调用

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
    print(f"生成了 {len(result.generated_tests)} 个测试用例")
    print(f"状态: {result.status}")

asyncio.run(main())
```

## 技术栈

| 组件 | 选型 | 用途 |
|------|------|------|
| Agent 编排 | Python asyncio | 多 Agent 流水线协调 |
| LLM | Anthropic Claude / OpenAI | 测试生成 + 文档分析 |
| Java AST | tree-sitter-java | Java 源码结构解析 |
| 测试执行 | subprocess → mvn/gradle | 运行生成的测试 |
| 覆盖率 | JaCoCo CSV 解析 | 覆盖率反馈闭环 |
| 模板引擎 | Jinja2 | JUnit 5 文件生成 |

## 开源协议

MIT
