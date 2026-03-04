"""OpenCode Overlord entry point."""

from overlord.orchestrator import AgentOrchestrator

__all__ = ["AgentOrchestrator"]


def main() -> None:
    """Print startup message."""
    print("OpenCode Overlord — use `overlord` CLI or import from overlord package.")


if __name__ == "__main__":
    main()
