
def test_extension_random_mechblock(md):
    # Some rough test to verify the parsing overall works okay enough.
    # This is most likely going to fail the tests sooner than later, but at least
    # breaking changes to regexes are likely going to be caught without checking
    # the actual parsed results in a browser.

    markdown = """```iron-vault-mechanics
move "[React Under Fire](datasworn:move:starforged\\/combat\\/react_under_fire)" {
    roll "Edge" action=6 adds=0 stat=2 vs1=6 vs2=1
    meter "Momentum" from=2 to=3
}
- "in control"
```"""

    expected_html = """<div class="ivm-mechanics">
<div class="ivm-move">
<div class="ivm-move-name">React Under Fire</div>
<div class="ivm-node">
<div class="ivm-roll ivm-roll-strong">Roll with Edge: 6 + 2 + 0 = 8 vs 6 | 1 strong </div>
</div>
<div class="ivm-node">
<div class="ivm-meter ivm-meter-increase"><i>Momentum</i>: 2 &rarr; 3</div>
</div>
</div>
<div class="ivm-ooc">// in control</div>
</div>"""

    html = md.convert(markdown)
    assert html == expected_html
