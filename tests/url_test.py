import pytest

from adr_generator.repo import InvalidRepoURL, parse_repo_url


@pytest.mark.parametrize(
    "text",
    [
        "https://github.com/pallets/flask",
        "https://github.com/pallets/flask/",
        "https://github.com/pallets/flask.git",
        "https://github.com/pallets/flask/tree/main/src",
        "  https://github.com/Pallets/Flask  ",
        "pallets/flask",
    ],
)
def test_valid_urls(text):
    ref = parse_repo_url(text)
    assert ref.owner == "pallets"
    assert ref.name == "flask"
    assert ref.full == "pallets/flask"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "hello",
        "https://github.com/onlyowner",
        "http://github.com/pallets/flask",
        "https://evil.com/pallets/flask",
        "ftp://github.com/pallets/flask",
        "https://github.com/a/b/../../c",
        "https://user:ghp_secret@github.com/pallets/flask",
    ],
)
def test_invalid_urls(text):
    with pytest.raises(InvalidRepoURL):
        parse_repo_url(text)