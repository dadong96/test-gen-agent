"""CLI interface for the test generation agent."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from src.main import run_test_generation


def _build_parser():
    parser = argparse.ArgumentParser(
        description="AI-powered JUnit 5 test case generator with coverage feedback loop",
    )
    subparsers = parser.add_subparsers(dest="command")

    gen = subparsers.add_parser("generate", help="Generate test cases for a Java project")
    gen.add_argument("--project", required=True, help="Path to the Java project")
    gen.add_argument("--prd", required=True, help="Path to the PRD document (Markdown)")
    gen.add_argument("--swagger", default=None, help="Path to the Swagger/OpenAPI spec (JSON/YAML)")
    gen.add_argument("--coverage-threshold", type=float, default=0.70, help="Target branch coverage threshold (default: 0.70)")
    gen.add_argument("--max-rounds", type=int, default=3, help="Max coverage retry rounds (default: 3)")
    gen.add_argument("--no-run", action="store_true", help="Generate tests but do not execute them")
    gen.add_argument("--dry-run", action="store_true", help="Parse docs only, do not generate tests")

    return parser


def parse_args():
    parser = _build_parser()
    return parser, parser.parse_args()


def validate_paths(args) -> bool:
    """Validate that required paths exist."""
    project = Path(args.project)
    prd = Path(args.prd)

    if not project.exists():
        print(f"Error: Project path does not exist: {project}", file=sys.stderr)
        return False
    if not prd.exists():
        print(f"Error: PRD file does not exist: {prd}", file=sys.stderr)
        return False
    if args.swagger:
        swagger = Path(args.swagger)
        if not swagger.exists():
            print(f"Error: Swagger file does not exist: {swagger}", file=sys.stderr)
            return False
    return True


async def async_main():
    parser, args = parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "generate":
        if not validate_paths(args):
            sys.exit(1)

        result = await run_test_generation(
            project_path=args.project,
            prd_path=args.prd,
            swagger_path=args.swagger,
            coverage_threshold=args.coverage_threshold,
            max_rounds=args.max_rounds,
            no_run=args.no_run,
            dry_run=args.dry_run,
        )

        print(f"\nStatus: {result.status}")
        print(f"Duration: {result.duration_seconds:.1f}s")
        print(f"Tests generated: {len(result.generated_tests)}")
        if result.token_summary:
            print(f"Tokens: {result.token_summary.get('total_tokens', 0)}")
        if result.error:
            print(f"Error: {result.error}", file=sys.stderr)

        sys.exit(0 if result.status in ("success", "dry_run") else 1)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
