import pytest

from overlord.dag import PRDependencyGraph
from overlord.exceptions import DependencyCycleError
from overlord.models import PRReference


def _pr(number: int, owner: str = "me", repo: str = "proj") -> PRReference:
    return PRReference(owner=owner, repo=repo, number=number)


class TestGetMergeOrder:
    def test_empty_graph(self) -> None:
        g = PRDependencyGraph()
        assert g.get_merge_order() == []

    def test_single_pr_no_deps(self) -> None:
        g = PRDependencyGraph()
        g.add_pr(_pr(1))
        order = g.get_merge_order()
        assert len(order) == 1
        assert order[0].number == 1

    def test_linear_chain(self) -> None:
        g = PRDependencyGraph()
        a, b, c = _pr(1), _pr(2), _pr(3)
        g.add_pr(a)
        g.add_pr(b, depends_on=[a])
        g.add_pr(c, depends_on=[b])
        order = g.get_merge_order()
        nums = [p.number for p in order]
        assert nums.index(1) < nums.index(2) < nums.index(3)

    def test_diamond(self) -> None:
        g = PRDependencyGraph()
        a, b, c, d = _pr(1), _pr(2), _pr(3), _pr(4)
        g.add_pr(a)
        g.add_pr(b, depends_on=[a])
        g.add_pr(c, depends_on=[a])
        g.add_pr(d, depends_on=[b, c])
        order = g.get_merge_order()
        nums = [p.number for p in order]
        assert nums.index(1) < nums.index(2)
        assert nums.index(1) < nums.index(3)
        assert nums.index(2) < nums.index(4)
        assert nums.index(3) < nums.index(4)

    def test_isolated_nodes(self) -> None:
        g = PRDependencyGraph()
        g.add_pr(_pr(1))
        g.add_pr(_pr(2))
        order = g.get_merge_order()
        assert len(order) == 2
        assert {p.number for p in order} == {1, 2}


class TestCycleDetection:
    def test_cycle_raises_dependency_cycle_error(self) -> None:
        g = PRDependencyGraph()
        a, b = _pr(1), _pr(2)
        g.add_pr(a, depends_on=[b])
        g.add_pr(b, depends_on=[a])
        with pytest.raises(DependencyCycleError, match="Circular dependency"):
            g.get_merge_order()

    def test_has_cycle_returns_true(self) -> None:
        g = PRDependencyGraph()
        a, b = _pr(1), _pr(2)
        g.add_pr(a, depends_on=[b])
        g.add_pr(b, depends_on=[a])
        assert g.has_cycle() is True

    def test_has_cycle_returns_false(self) -> None:
        g = PRDependencyGraph()
        a, b = _pr(1), _pr(2)
        g.add_pr(a)
        g.add_pr(b, depends_on=[a])
        assert g.has_cycle() is False


class TestParseDependencies:
    def test_depends_on_hash(self) -> None:
        g = PRDependencyGraph()
        deps = g.parse_dependencies_from_body(
            "Depends-On: #42", default_owner="me", default_repo="proj"
        )
        assert len(deps) == 1
        assert deps[0] == PRReference(owner="me", repo="proj", number=42)

    def test_depends_on_url(self) -> None:
        g = PRDependencyGraph()
        body = "Depends-On: https://github.com/acme/widgets/pull/99"
        deps = g.parse_dependencies_from_body(body)
        assert len(deps) == 1
        assert deps[0] == PRReference(owner="acme", repo="widgets", number=99)

    def test_requires_shorthand(self) -> None:
        g = PRDependencyGraph()
        deps = g.parse_dependencies_from_body("Requires: acme/widgets#7")
        assert len(deps) == 1
        assert deps[0] == PRReference(owner="acme", repo="widgets", number=7)

    def test_no_deps_in_body(self) -> None:
        g = PRDependencyGraph()
        deps = g.parse_dependencies_from_body("Just a regular PR body.")
        assert deps == []

    def test_multiple_deps_mixed_formats(self) -> None:
        g = PRDependencyGraph()
        body = (
            "This PR:\n"
            "Depends-On: #10\n"
            "Depends-On: https://github.com/org/repo/pull/20\n"
            "Requires: ext/lib#30\n"
        )
        deps = g.parse_dependencies_from_body(body, default_owner="me", default_repo="proj")
        assert len(deps) == 3
        assert deps[0].number == 10
        assert deps[1] == PRReference(owner="org", repo="repo", number=20)
        assert deps[2] == PRReference(owner="ext", repo="lib", number=30)


class TestGetReady:
    def test_returns_no_dep_prs(self) -> None:
        g = PRDependencyGraph()
        a, b, c = _pr(1), _pr(2), _pr(3)
        g.add_pr(a)
        g.add_pr(b, depends_on=[a])
        g.add_pr(c)
        ready_nums = {p.number for p in g.get_ready()}
        assert ready_nums == {1, 3}

    def test_all_have_deps(self) -> None:
        g = PRDependencyGraph()
        a, b = _pr(1), _pr(2)
        g.add_pr(a, depends_on=[b])
        g.add_pr(b, depends_on=[a])
        ready = g.get_ready()
        assert ready == []
