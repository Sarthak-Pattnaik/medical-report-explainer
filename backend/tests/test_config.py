from app.core.config import Settings


def make_settings(cors_origins: str) -> Settings:
    return Settings(
        DATABASE_URL="postgresql://test:test@localhost/test",
        JWT_SECRET_KEY="test-secret",
        CORS_ORIGINS=cors_origins,
    )


def test_cors_origins_are_split_and_trimmed():
    settings = make_settings(" https://a.com , https://b.com ")

    assert settings.cors_origins == ["https://a.com", "https://b.com"]


def test_cors_origins_ignore_empty_entries():
    settings = make_settings("https://a.com,,")

    assert settings.cors_origins == ["https://a.com"]