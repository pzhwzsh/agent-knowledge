from fastapi import HTTPException

from app.collectors import web as web_collector
from app.collectors.web import WebPageCollector
from app.core.url_security import validate_public_http_url


class FakeResponse:
    url = "http://127.0.0.1/admin"
    text = "<html><head><title>Redirected</title></head><body>secret internal content</body></html>"

    def raise_for_status(self) -> None:
        return None


class RedirectingClient:
    def get(self, source: str) -> FakeResponse:
        return FakeResponse()


def test_web_collector_rejects_private_final_redirect_url(monkeypatch) -> None:
    def fake_validate(url: str) -> str:
        if url == "https://public.example/source":
            return url
        return validate_public_http_url(url)

    monkeypatch.setattr(web_collector, "validate_public_http_url", fake_validate)
    collector = WebPageCollector(client=RedirectingClient())

    try:
        collector.fetch_page("https://public.example/source")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "Private or reserved" in str(exc.detail) or "Localhost" in str(exc.detail)
    else:
        raise AssertionError("Expected private redirected URL to be rejected")
