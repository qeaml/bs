# qcbs

**q**eaml's **C**/C++ **B**uild **S**ystem

## Setup

To prepare a project to be build via qcbs, create a `qcbs.yaml` file. It will
tell qcbs to how to build, the tool will figure everything else out. Required
values are marked with an asterisk: `*`. You can see an example program compiled
with qcbs in the [`example` directory](example).

```yaml
exe: '' # * base name of the executable, WITHOUT any extension

cc: '' # * name of the compiler to use.
       # currently can be one of: 'cl' (MSVC), 'clang', 'gcc'

root: '' # the root of the project. this is relative to wherever this file is.
         # all other paths in this file are relative to this path. if this is
         # not specified, the directory in which qcbs was invoked is used.

src: '' # location of the source files. if not specified, the root directory is
        # used instead.

bin: '' # where to place compiled executables (object files NOT included). alike
        # src, root is used if this is omitted

obj: '' # where to place compiled object files. if this is omitted, bin is used
        # instead.

lib: [] # list of libraries to link against, just their names, like "SDL2":
        # no extensions. this may be omitted for empty lists

incl: [] # paths to add to the include search paths. this may be omitted for
         # empty lists
```

## Usage

### Building a project

To build whatever project is in the working directory:

```console
$ qcbs
$ py -m qcbs # (interchangable, although the above is preffered)
```

If you wish to build a project in a different directory:

```console
$ qcbs /user/Timmy/projects/my-app
```

If you wish to build the project in the current working directory with debug
flags:

```console
$ qcbs --debug
```

If you wish to clean the build directory before building (effectively
completely rebuilding the entire project):

```console
$ qcbs --clean
```

`clean` and `debug can be combined, in any order:

```console
$ qcbs --clean --debug
$ qcbs /user/Timmy/projects/my-app --debug
$ qcbs .. --debug --clean
$ qcbs cooltool --clean
```

### Initializing a project

You can use `init` to create a file structure based on the command-line
arguments passed to qcbs:

```console
$ git init my-project
$ cd my-project
$ qcbs --init --exe=my-app --cc=clang --src=source --incl=include --bin=target --obj=target/build
Initializing project at .
* source
* target
* target\build
* include
* qcbs.yaml
Finshed in 0.0s
```
