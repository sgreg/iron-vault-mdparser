from ironvaultmd.parsers.blocks import (
    ActorBlockParser,
    MoveBlockParser,
    OracleGroupBlockParser,
    OracleBlockParser,
    OraclePromptBlockParser,
)
from ironvaultmd.parsers.templater import templater
from utils import element_text


def test_parser_actor(ctx):
    parser = ActorBlockParser()

    assert parser.block_name == "Actor"
    assert parser.regex

    data = 'name="[[link|Character Name]]"'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-actor"

    children = element.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-actor-name"
    assert children[0].text == "Character Name"

    data = 'Invalid data'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-block"

    children = element.findall("div")
    assert len(children) == 0


def test_parser_move(ctx):
    parser = MoveBlockParser()

    assert parser.block_name == "Move"
    assert parser.regex

    data = '"[Move Name](Move Link)"'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-move"

    children = element.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-move-name"
    assert children[0].text == "Move Name"

    data = 'Invalid data'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-block"

    children = element.findall("div")
    assert len(children) == 0

def test_parser_move_no_roll(ctx):
    parser = MoveBlockParser()

    assert parser.block_name == "Move"
    assert parser.regex

    data = '"[Move Name](Move Link)"'
    root = parser.begin(ctx, data)
    ctx.push("move", root)

    ctx.roll.rolled = False
    parser.finalize(ctx)
    element = ctx.parent

    assert element is not None
    # No roll context involved here, so move result classes aren't added in finalize()
    assert element.get("class") == "ivm-move"

    children = element.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-move-name"
    assert children[0].text == "Move Name"

def test_parser_move_with_roll(ctx):
    parser = MoveBlockParser()

    assert parser.block_name == "Move"
    assert parser.regex

    data = '"[Move Name](Move Link)"'
    root = parser.begin(ctx, data)
    ctx.push("move", root)

    ctx.roll.roll(5, 2, 0, 3, 8) # total 7 vs 3 | 8, expect weak hit
    parser.finalize(ctx)
    element = ctx.parent

    assert element is not None
    assert element.get("class") == "ivm-move ivm-move-result-weak"

    children = element.findall("div")
    # Expect 1 div with the move name
    # In a real scenario there'd also be the actual roll, but we're not parsing nodes here, only invoke roll context
    assert len(children) == 1
    assert children[0].get("class") == "ivm-move-name"
    assert children[0].text == "Move Name"

def test_parser_oracle_group(ctx):
    parser = OracleGroupBlockParser()

    assert parser.block_name == "Oracle Group"
    assert parser.regex

    data = 'name="Group Name"'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-oracle-block"

    children = element.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    assert children[0].text == "Oracle: Group Name"

    data = 'Invalid data'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-block"

    children = element.findall("div")
    assert len(children) == 0

def test_parser_oracle(ctx):
    parser = OracleBlockParser()

    assert parser.block_name == "Oracle"
    assert parser.regex

    data = 'name="[Oracle Name](datasworn:link)" result="Oracle Result" roll=55'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-oracle-block"

    children = element.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    for sub in ["Oracle Name", "Oracle Result", "55"]:
        assert sub in children[0].text

    data = 'name="Will [[ignore|some clock]] advance?" result="Clock Result" roll=23'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-oracle-block"

    children = element.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    for sub in ["Will some clock advance", "Clock Result", "23"]:
        assert sub in children[0].text

    data = 'Invalid data'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-block"

    children = element.findall("div")
    assert len(children) == 0

def test_parser_oracle_prompt(ctx):
    parser = OraclePromptBlockParser()

    assert parser.block_name == "Oracle Prompt"
    assert parser.regex

    data = '"My Oracle Prompt"'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-oracle-block"

    children = element.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    assert children[0].text == "Oracle: My Oracle Prompt"

    data = 'Invalid data'
    element = parser.begin(ctx, data)
    assert element is not None
    assert element.get("class") == "ivm-block"

    children = element.findall("div")
    assert len(children) == 0