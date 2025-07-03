import pytest

from web_server.http import Response


@pytest.mark.parametrize(
    "protocol_version, status, headers, expected",
    [
        (
            (1, 0),
            "200 OK",
            [("Content-Type", "text/plain")],
            ((1, 0), "200 OK", [("Content-Type", "text/plain")]),
        ),
        (
            (1, 1),
            "404 Not Found",
            [("Content-Type", "text/html")],
            ((1, 1), "404 Not Found", [("Content-Type", "text/html")]),
        ),
        (
            (2, 0),
            "500 Internal Server Error",
            [("Content-Type", "application/json")],
            (
                (2, 0),
                "500 Internal Server Error",
                [("Content-Type", "application/json")],
            ),
        ),
    ],
)
def test_draft(
    protocol_version: tuple[int, int],
    status: str,
    headers: list[tuple[str, str]],
    expected: tuple[tuple[int, int], str, list[tuple[str, str]]],
):
    response = Response.draft(
        protocol_version=protocol_version,
        status=status,
        headers=headers,
    )

    version, status, headers = expected
    assert response.version == version
    assert response.status == status
    assert response.headers == headers
    assert response.body is None
