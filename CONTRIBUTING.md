# Contributing

*For basic contribution information, refer to the
[main "Contributing" document][main].*

## Before Pushing

Make sure the code passes type checking:

```console
$ mypy qcbs --strict --explicit-package-bases
Success: no issues found [...]
```

Ensure the example compiles:

```console
$ qcbs example
* main.o
* rng.o
* my-app
Successfully built in 0.4s
```

[main]: https://github.com/qeaml/qeaml/blob/main/CONTRIBUTING.md
