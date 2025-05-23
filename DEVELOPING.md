# Developing ironvaultmd

## tl;dr

```shell
$ python -m venv venv
$ . ./venv/bin/activate
$ (venv) $ pip install -r requirements-dev.txt
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

### Tests

#### Just the tests

Tests are run with `pytest` and its details are set up in [`pytest.ini`](pytest.ini) 

```shell
(venv) $ pytest
```

#### With code coverage

Code coverage of the executed unit tests is collected with `coverage`, with details set up in [`.coveragerc`](.coveragerc)

```shell
(venv) coverage run
```

Results can be displayed as a text table via
```shell
(venv) coverage report
```
or written to an XML file to pass on to e.g. SonarQube via
```shell
(venv) coverage xml
```

