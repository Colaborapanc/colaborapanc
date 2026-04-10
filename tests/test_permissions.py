from types import SimpleNamespace
from mapping.permissions import IsReviewerOrAdmin


class FakeGroupManager:
    def __init__(self, names):
        self._names = set(names)

    def filter(self, name):
        return SimpleNamespace(exists=lambda: name in self._names)


class FakeUser:
    def __init__(self, authenticated=True, superuser=False, groups=None):
        self.is_authenticated = authenticated
        self.is_superuser = superuser
        self.groups = FakeGroupManager(groups or [])


def test_permission_deny_anonymous():
    perm = IsReviewerOrAdmin()
    req = SimpleNamespace(user=FakeUser(authenticated=False))
    assert perm.has_permission(req, None) is False


def test_permission_allow_reviewer_group():
    perm = IsReviewerOrAdmin()
    req = SimpleNamespace(user=FakeUser(groups=['Revisor']))
    assert perm.has_permission(req, None) is True


def test_permission_allow_superuser():
    perm = IsReviewerOrAdmin()
    req = SimpleNamespace(user=FakeUser(superuser=True))
    assert perm.has_permission(req, None) is True
