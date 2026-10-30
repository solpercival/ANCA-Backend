"""Settings.postgres_dsn with a password that has URL-special characters."""

from psycopg.conninfo import conninfo_to_dict
from sqlalchemy.engine import make_url

from rag_engine.config import Settings

PASSWORD = "p@ss:w/rd%312"


def test_special_characters_in_the_password_stay_in_the_password():
    dsn = Settings(postgres_password=PASSWORD, postgres_host="postgres").postgres_dsn

    libpq = conninfo_to_dict(dsn)
    assert (libpq["host"], libpq["password"]) == ("postgres", PASSWORD)
    url = make_url(dsn.replace("postgresql://", "postgresql+psycopg://", 1))
    assert (url.host, url.password) == ("postgres", PASSWORD)
