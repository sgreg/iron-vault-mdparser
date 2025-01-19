def test_markdown(md):
    html = md.convert("# hello")
    assert(html == "<h1>hello</h1>")
