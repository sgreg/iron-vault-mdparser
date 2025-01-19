
def test_markdown(md):
    html = md.convert("# hello")
    assert(html == "<h1>hello</h1>")


def test_mech_block(mechproc):
    lines = [
        "test run",
        "without any changes from the preprocessor"
    ]

    ret = mechproc.run(lines)
    assert ret == lines
