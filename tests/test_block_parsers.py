from ironvaultmd.parsers.blocks import (
    ActorBlockParser,
    MoveBlockParser,
    OracleGroupBlockParser,
    OracleBlockParser,
    OraclePromptBlockParser,
)
from utils import verify_is_dummy_block_element


def test_parser_actor(ctx):
    parser = ActorBlockParser()
    assert parser.block_name == "Actor"

    data = 'name="[[link|Character Name]]"'
    element, args = parser.begin(ctx, data)
    verify_is_dummy_block_element(element)

    # Verify arguments were parsed as expected
    assert "name" in args.keys()
    assert args["name"] == "Character Name"

    ctx.push(parser.block_name, element, args)
    assert ctx.name == "Actor"
    assert ctx.parent == element
    verify_is_dummy_block_element(ctx.parent)

    parser.finalize(ctx)

    # Verify ctx.parent was turned into div with ivm-actor class
    assert ctx.parent is not None
    assert ctx.parent.get("class") == "ivm-actor"

    # Verify ivm-actor-name class div was added
    children = ctx.parent.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-actor-name"
    assert children[0].text == "Character Name"

def test_parser_move_no_roll(ctx):
    parser = MoveBlockParser()
    assert parser.block_name == "Move"

    data = '"[Move Name](Move Link)"'
    element, args = parser.begin(ctx, data)
    verify_is_dummy_block_element(element)

    # Verify arguments were parsed as expected
    assert "name" in args.keys()
    assert args["name"] == "Move Name"

    ctx.push(parser.block_name, element, args)
    parser.finalize(ctx)

    assert ctx.parent.get("class") == "ivm-move"

    children = ctx.parent.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-move-name"
    assert children[0].text == "Move Name"

def test_parser_move_with_roll(ctx):
    parser = MoveBlockParser()
    assert parser.block_name == "Move"

    data = '"[Move Name](Move Link)"'
    element, args = parser.begin(ctx, data)
    verify_is_dummy_block_element(element)

    # Verify arguments were parsed as expected
    assert "name" in args.keys()
    assert args["name"] == "Move Name"

    ctx.push(parser.block_name, element, args)
    ctx.roll.roll(5, 2, 0, 3, 8) # total 7 vs 3 | 8, expect weak hit
    parser.finalize(ctx)

    assert ctx.parent.get("class") == "ivm-move ivm-move-result-weak"

    children = ctx.parent.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-move-name"
    assert children[0].text == "Move Name"

def test_parser_oracle_group(ctx):
    parser = OracleGroupBlockParser()
    assert parser.block_name == "Oracle Group"

    data = 'name="Group Name"'
    element, args = parser.begin(ctx, data)
    verify_is_dummy_block_element(element)

    assert "oracle" in args.keys()
    assert args["oracle"] == "Group Name"

    ctx.push(parser.block_name, element, args)
    parser.finalize(ctx)

    assert ctx.parent is not None
    assert ctx.parent.get("class") == "ivm-oracle-block"

    children = ctx.parent.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    assert children[0].text == "Oracle: Group Name"

def test_parser_oracle_block_name(ctx):
    parser = OracleBlockParser()
    assert parser.block_name == "Oracle"

    data = 'name="[Oracle Name](datasworn:link)" result="Oracle Result" roll=55'
    element, args = parser.begin(ctx, data)
    verify_is_dummy_block_element(element)

    assert "oracle" in args.keys()
    assert args["oracle"] == "Oracle Name"

    ctx.push(parser.block_name, element, args)
    parser.finalize(ctx)

    assert ctx.parent is not None
    assert ctx.parent.get("class") == "ivm-oracle-block"

    children = ctx.parent.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    for sub in ["Oracle Name", "Oracle Result", "55"]:
        assert sub in children[0].text

def test_parser_oracle_block_text(ctx):
    parser = OracleBlockParser()
    assert parser.block_name == "Oracle"

    data = 'name="Will [[ignore|some clock]] advance?" result="Clock Result" roll=23'
    element, args = parser.begin(ctx, data)
    verify_is_dummy_block_element(element)

    assert "oracle" in args.keys()
    keys = ["oracle", "result", "roll"]
    assert all(key in args.keys() for key in keys)
    assert args["oracle"] == "Will some clock advance?"

    assert args["result"] == "Clock Result"
    assert args["roll"] == "23"

    ctx.push(parser.block_name, element, args)
    parser.finalize(ctx)

    assert ctx.parent is not None
    assert ctx.parent.get("class") == "ivm-oracle-block"

    children = ctx.parent.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    for sub in ["Will some clock advance", "Clock Result", "23"]:
        assert sub in children[0].text

def test_parser_oracle_prompt(ctx):
    parser = OraclePromptBlockParser()
    assert parser.block_name == "Oracle Prompt"

    data = '"My Oracle Prompt"'
    element, args = parser.begin(ctx, data)
    verify_is_dummy_block_element(element)

    ctx.push(parser.block_name, element, args)
    parser.finalize(ctx)

    assert ctx.parent is not None
    assert ctx.parent.get("class") == "ivm-oracle-block"

    children = ctx.parent.findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    assert children[0].text == "Oracle: My Oracle Prompt"
