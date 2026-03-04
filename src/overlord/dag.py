"""PR dependency graph using Python stdlib graphlib.TopologicalSorter."""

import re
from graphlib import CycleError, TopologicalSorter

from overlord.exceptions import DependencyCycleError
from overlord.models import PRReference


class PRDependencyGraph:
    """PR dependency graph using Python stdlib graphlib.TopologicalSorter.

    Supports Depends-On, Requires syntax for PR body parsing.
    """

    def __init__(self) -> None:
        self._graph: dict[PRReference, set[PRReference]] = {}

    def add_pr(
        self,
        pr: PRReference,
        depends_on: list[PRReference] | None = None,
    ) -> None:
        """Add a PR and its dependencies to the graph."""
        if pr not in self._graph:
            self._graph[pr] = set()
        if depends_on:
            for dep in depends_on:
                self._graph[pr].add(dep)
                if dep not in self._graph:
                    self._graph[dep] = set()

    def get_merge_order(self) -> list[PRReference]:
        """Return PRs in topological order (safe to merge in this order).

        Raises DependencyCycleError if a cycle is detected.
        """
        ts: TopologicalSorter[PRReference] = TopologicalSorter()
        for pr, deps in self._graph.items():
            ts.add(pr, *deps)
        try:
            return list(ts.static_order())
        except CycleError as e:
            raise DependencyCycleError(f"Circular dependency detected: {e}") from e

    def parse_dependencies_from_body(
        self,
        body: str,
        default_owner: str = "",
        default_repo: str = "",
    ) -> list[PRReference]:
        """Parse PR dependency references from PR body text.

        Supports:
        - Depends-On: #42 (same-repo PR)
        - Depends-On: https://github.com/{owner}/{repo}/pull/{N}
        - Requires: {owner}/{repo}#{N}
        """
        deps: list[PRReference] = []

        # Pattern 1: Depends-On: #42 (same repo shorthand)
        for match in re.finditer(r"Depends-On:\s+#(\d+)", body):
            deps.append(
                PRReference(
                    owner=default_owner,
                    repo=default_repo,
                    number=int(match.group(1)),
                )
            )

        # Pattern 2: Depends-On: https://github.com/owner/repo/pull/N
        for match in re.finditer(
            r"Depends-On:\s+https://github\.com/([^/]+)/([^/]+)/pull/(\d+)",
            body,
        ):
            deps.append(
                PRReference(
                    owner=match.group(1),
                    repo=match.group(2),
                    number=int(match.group(3)),
                )
            )

        # Pattern 3: Requires: owner/repo#N
        for match in re.finditer(r"Requires:\s+([^/\s]+)/([^#\s]+)#(\d+)", body):
            deps.append(
                PRReference(
                    owner=match.group(1),
                    repo=match.group(2),
                    number=int(match.group(3)),
                )
            )

        return deps

    def has_cycle(self) -> bool:
        """Check if the graph has a cycle without raising."""
        ts: TopologicalSorter[PRReference] = TopologicalSorter()
        for pr, deps in self._graph.items():
            ts.add(pr, *deps)
        try:
            list(ts.static_order())
        except CycleError:
            return True
        return False

    def get_ready(self) -> list[PRReference]:
        """Get PRs that have all dependencies satisfied (ready to merge).

        Returns PRs with no outstanding dependencies.
        """
        ready: list[PRReference] = []
        for pr, deps in self._graph.items():
            if not deps:
                ready.append(pr)
        return ready
