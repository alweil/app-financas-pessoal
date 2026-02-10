def test_homepage_title(page):
    page.goto("http://localhost:8000")
    assert page.title() == "Assessor Financeiro"
