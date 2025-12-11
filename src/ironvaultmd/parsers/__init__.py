"""Iron Vault mechanics parsing package.

This package contains parsing primitives and concrete parsers used by the
Iron Vault Markdown extension to transform fenced
```iron-vault-mechanics sections into structured HTML via Jinja templates.

Components:
- Base classes: `NodeParser` and `MechanicsBlockParser` in `base.py`.
- Block parsers for high‑level constructs (actors, moves, oracles) in `blocks.py`.
- Node parsers for line‑level mechanics (roll, reroll, progress, clocks, etc.) in `nodes.py`.
- A parsing `Context` shared across nested blocks in `context.py`.
- A minimal templating helper with default and user‑provided templates in `templater.py`.

In normal use you do not import these parsers directly. Instead, register the
Markdown preprocessor and block processor from
`ironvaultmd.processors.mechanics`, which will delegate to this package.

Example:
    ```python
    from markdown import Markdown
    from ironvaultmd.processors.mechanics import (
        IronVaultMechanicsPreprocessor,
        IronVaultMechanicsBlockProcessor,
    )

    md = Markdown()
    md.preprocessors.register(IronVaultMechanicsPreprocessor(md), 'iv-mech-pre', 36)
    md.parser.blockprocessors.register(IronVaultMechanicsBlockProcessor(md.parser), 'iv-mech', 175)
    ```
"""
