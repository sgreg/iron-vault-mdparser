# iron-vault-mdparser
[![Quality Gate Status](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=alert_status&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Coverage](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=coverage&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Security Hotspots](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=security_hotspots&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Reliability Issues](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=software_quality_reliability_issues&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Maintainability Issues](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=software_quality_maintainability_issues&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)
[![Security Issues](https://sonarqube.craplab.fi/api/project_badges/measure?project=iron-vault-mdparser&metric=software_quality_security_issues&token=sqb_09511c290a6a0c81316431640636eeed4db43f92)](https://sonarqube.craplab.fi/dashboard?id=iron-vault-mdparser)

A [Python-Markdown](https://pypi.org/project/Markdown/) ([github](https://github.com/Python-Markdown/markdown)) extension to parse Markdown files from the [Iron Vault](https://ironvault.quest/) ([github](https://github.com/iron-vault-plugin/iron-vault)) Obsidian plugin.

Mainly parses anything within ` ```iron-vault-mechanics ... ``` ` blocks, but als frontmatter YAML.


## Setup

Dependencies to use the extension / run the sample parser are listed in `requirements.txt`. It's recommended to set up a virtual environment.

```shell
$ python -m venv venv
$ . ./venv/bin/activate
$ (venv) $ pip install -r requirements.txt
```

For dependencies needed for development, check the Development section below.

## Usage

```shell
$ python ./ironvault.py /path/to/vault/Journals/Session.md /tmp/Session.html
```


## Development

### Dependencies

Dependencies are separated to those required to run the extension and sample parser, and those that are
required for full development and CI pipeline runs (unit tests, coverage), and listed in `requirements.in`
and `requirements-dev.in` respectively. Those are on high level only, and `pip-tools` is used to create a
full list of requirements from it, which can then be passed `pip install -f`.

If you just want to hack some stuff together, the runtime dependencies are probably all you need, but if
you want to e.g. add and run tests, go with the `-dev` ones. To make life easier, a set of precompiled
`requirements.txt` and `requirements-dev.txt` files are added to the repository.

#### pip-tools

Dependencies are managed with `pip-tools`, which needs to be installed first, and latest now the virtual
environment is very recommended.

```shell
$ python -m venv venv
$ . ./venv/bin/activate
(venv) $ pip install pip-tools
```

To compile and install runtime requirements:

```shell
(venv) $ pip-compile requirements.in -o requirements.txt
(venv) $ pip install -r requirements.txt
```

To compile and install both runtime and development requirements:

```shell
(venv) $ pip-compile requirements.in requirements-dev.in -o requirements-dev.txt
(venv) $ pip install -r requirements-dev.txt
```
