from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserContext:
    """Identity from ingress (oauth2-proxy) for retrieval ABAC prep (Phase 1D.2)."""

    subject: str
    email: str = ""
    groups: tuple[str, ...] = ()

    def retrieval_principals(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for value in (self.subject, self.email, *self.groups):
            token = (value or "").strip()
            if token and token not in seen:
                seen.add(token)
                out.append(token)
        return out


def parse_user_context_from_headers(
    *,
    x_auth_request_user: str | None = None,
    x_auth_request_email: str | None = None,
    x_auth_request_groups: str | None = None,
) -> UserContext | None:
    subject = (x_auth_request_user or x_auth_request_email or "").strip()
    if not subject:
        return None
    email = (x_auth_request_email or "").strip()
    groups_raw = (x_auth_request_groups or "").strip()
    groups = tuple(g.strip() for g in groups_raw.split(",") if g.strip())
    return UserContext(subject=subject, email=email, groups=groups)
