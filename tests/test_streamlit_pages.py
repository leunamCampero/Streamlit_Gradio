"""Runs every Streamlit page headlessly and checks it renders without exceptions.

    python -m pytest tests -q
"""
import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["views/home.py", "views/network.py", "views/model.py", "views/tits2025.py",
         "views/ecc2025.py", "views/cdc2025.py", "views/itsc2025.py", "views/itsc2026.py"]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = AppTest.from_file("../streamlit_app/app.py", default_timeout=60)
    at.run()
    at.switch_page(page).run()
    assert not at.exception, [e.message for e in at.exception]
