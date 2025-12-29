from ironvaultmd.parsers.blocks import (
    ActorBlockParser,
    MoveBlockParser,
    OracleGroupBlockParser,
    OracleBlockParser,
    OraclePromptBlockParser,
)
from ironvaultmd.parsers.templater import Templater, TemplateOverrides, set_templater
from utils import verify_is_dummy_block_element


def test_parser_actor(ctx):
    parser = ActorBlockParser()
    assert parser.names.name == "Actor"
    assert parser.names.parser == "actor"
    assert parser.names.template == "actor"

    data = 'name="[[link|Character Name]]"'
    parser.begin(ctx, data)
    verify_is_dummy_block_element(ctx.parent)

    # Verify arguments were parsed as expected
    assert "name" in ctx.args.keys()
    assert ctx.args["name"] == "Character Name"

    assert ctx.names == parser.names
    verify_is_dummy_block_element(ctx.parent)

    parser.finalize(ctx)

    # Verify ctx.parent was turned into div with ivm-actor class
    blocks = ctx.parent.findall("div")
    assert len(blocks) == 1
    assert blocks[0].get("class") == "ivm-actor"

    # Verify ivm-actor-name class div was added
    children = blocks[0].findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-actor-name"
    assert children[0].text == "Character Name"

def test_parser_move_no_roll(ctx):
    parser = MoveBlockParser()
    assert parser.names.name == "Move"
    assert parser.names.parser == "move"
    assert parser.names.template == "move"

    data = '"[Move Name](Move Link)"'
    parser.begin(ctx, data)
    verify_is_dummy_block_element(ctx.parent)

    # Verify arguments were parsed as expected
    assert "name" in ctx.args.keys()
    assert ctx.args["name"] == "Move Name"

    parser.finalize(ctx)

    # Verify the move is rendered without a result class
    blocks = ctx.parent.findall("div")
    assert len(blocks) == 1
    assert blocks[0].get("class") == "ivm-move"

    # Verify just the move name is in the block
    children = blocks[0].findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-move-name"
    assert children[0].text == "Move Name"

def test_parser_move_with_roll(ctx):
    parser = MoveBlockParser()
    assert parser.names.name == "Move"
    assert parser.names.parser == "move"
    assert parser.names.template == "move"

    data = '"[Move Name](Move Link)"'
    parser.begin(ctx, data)
    verify_is_dummy_block_element(ctx.parent)

    # Verify arguments were parsed as expected
    assert "name" in ctx.args.keys()
    assert ctx.args["name"] == "Move Name"

    ctx.roll.roll(5, 2, 0, 3, 8) # total 7 vs 3 | 8, expect weak hit
    parser.finalize(ctx)

    # Verify the move is rendered with a result class
    blocks = ctx.parent.findall("div")
    assert len(blocks) == 1
    assert blocks[0].get("class") == "ivm-move ivm-move-result-weak"

    # Verify the move name and a roll result node are in the block
    children = blocks[0].findall("div")
    assert len(children) == 2
    assert children[0].get("class") == "ivm-move-name"
    assert children[0].text == "Move Name"
    assert children[1].get("class") == "ivm-roll-result ivm-roll-weak"
    assert "Roll result" in children[1].text

def test_parser_move_with_roll_no_result_template(ctx):
    parser = MoveBlockParser()
    templater = Templater(overrides=TemplateOverrides(roll_result=''))
    set_templater(templater)

    data = '"[Move Name](Move Link)"'
    parser.begin(ctx, data)
    ctx.roll.roll(5, 2, 0, 3, 8) # total 7 vs 3 | 8, expect weak hit
    parser.finalize(ctx)

    # Verify the move is rendered with a result class
    blocks = ctx.parent.findall("div")
    assert len(blocks) == 1
    assert blocks[0].get("class") == "ivm-move ivm-move-result-weak"

    # Verify the move name but not the roll result node are in the block
    children = blocks[0].findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-move-name"
    assert children[0].text == "Move Name"

def test_parser_oracle_group(ctx):
    parser = OracleGroupBlockParser()
    assert parser.names.name == "Oracle Group"
    assert parser.names.parser == "oracle-group"
    assert parser.names.template == "oracle"

    data = 'name="Group Name"'
    parser.begin(ctx, data)
    verify_is_dummy_block_element(ctx.parent)

    assert "oracle" in ctx.args.keys()
    assert ctx.args["oracle"] == "Group Name"

    parser.finalize(ctx)

    blocks = ctx.parent.findall("div")
    assert len(blocks) == 1
    assert blocks[0].get("class") == "ivm-oracle-block"

    children = blocks[0].findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    assert children[0].text == "Oracle: Group Name"

def test_parser_oracle_block_name(ctx):
    parser = OracleBlockParser()
    assert parser.names.name == "Oracle"
    assert parser.names.parser == "oracle"
    assert parser.names.template == "oracle"

    data = 'name="[Oracle Name](datasworn:link)" result="Oracle Result" roll=55'
    parser.begin(ctx, data)
    verify_is_dummy_block_element(ctx.parent)

    assert "oracle" in ctx.args.keys()
    assert ctx.args["oracle"] == "Oracle Name"

    parser.finalize(ctx)

    blocks = ctx.parent.findall("div")
    assert len(blocks) == 1
    assert blocks[0].get("class") == "ivm-oracle-block"

    children = blocks[0].findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    for sub in ["Oracle Name", "Oracle Result", "55"]:
        assert sub in children[0].text

def test_parser_oracle_block_text(ctx):
    parser = OracleBlockParser()
    assert parser.names.name == "Oracle"
    assert parser.names.parser == "oracle"
    assert parser.names.template == "oracle"

    data = 'name="Will [[ignore|some clock]] advance?" result="Clock Result" roll=23'
    parser.begin(ctx, data)
    verify_is_dummy_block_element(ctx.parent)

    assert "oracle" in ctx.args.keys()
    keys = ["oracle", "result", "roll"]
    assert all(key in ctx.args.keys() for key in keys)
    assert ctx.args["oracle"] == "Will some clock advance?"

    assert ctx.args["result"] == "Clock Result"
    assert ctx.args["roll"] == 23

    parser.finalize(ctx)

    blocks = ctx.parent.findall("div")
    assert len(blocks) == 1
    assert blocks[0].get("class") == "ivm-oracle-block"

    children = blocks[0].findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    for sub in ["Will some clock advance", "Clock Result", "23"]:
        assert sub in children[0].text

def test_parser_oracle_prompt(ctx):
    parser = OraclePromptBlockParser()
    assert parser.names.name == "Oracle Prompt"
    assert parser.names.parser == "-"
    assert parser.names.template == "oracle"

    data = '"My Oracle Prompt"'
    parser.begin(ctx, data)
    verify_is_dummy_block_element(ctx.parent)

    assert "prompt" in ctx.args.keys()
    assert ctx.args["prompt"] == "My Oracle Prompt"

    parser.finalize(ctx)

    blocks = ctx.parent.findall("div")
    assert len(blocks) == 1
    assert blocks[0].get("class") == "ivm-oracle-block"

    children = blocks[0].findall("div")
    assert len(children) == 1
    assert children[0].get("class") == "ivm-oracle-name"
    assert children[0].text == "Oracle: My Oracle Prompt"
