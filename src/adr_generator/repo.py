import re
from dataclasses import dataclass
from urllib.parse import urlparse

_NAME_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,100}")
_OWNER_PATTERN = re.compile(r"[A-Za-z0-9-]{1,39}")
_HINT = "Please enter a URL like https://github.com/owner/repo"


class InvalidRepoURL(ValueError):
    """Raised when the text is not a valid GitHub repository URL."""


@dataclass(frozen=True)
class RepoRef:
    owner: str
    name: str

    @property
    def full(self) -> str:
        return f"{self.owner}/{self.name}"


def parse_repo_url(text: str) -> RepoRef:
    text = (text or "").strip()
    if not text:
        raise InvalidRepoURL(_HINT)

    # shorthand like "pallets/flask"
    if "://" not in text:
        text = f"https://github.com/{text}"

    try:
        parsed = urlparse(text)
        host = parsed.hostname
        has_credentials = parsed.username is not None or parsed.password is not None
    except ValueError:
        raise InvalidRepoURL(_HINT) from None

    if parsed.scheme != "https" or host != "github.com":
        raise InvalidRepoURL("Only https://github.com URLs are supported.")
    if has_credentials:
        raise InvalidRepoURL("Do not include a username or token in the URL.")

    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise InvalidRepoURL(_HINT)

    owner, name = parts[0], parts[1]
    if name.endswith(".git"):
        name = name[:-4]

    if not _OWNER_PATTERN.fullmatch(owner) or not _NAME_PATTERN.fullmatch(name) or name in {".", ".."}:
        raise InvalidRepoURL(_HINT)
    if ".." in parts:
        raise InvalidRepoURL(_HINT)

    return RepoRef(owner.lower(), name.lower())