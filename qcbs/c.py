from qcbs.common import *
from pathlib import Path
from dataclasses import dataclass
import subprocess

@dataclass
class Flagset:
  """ Contains commandline flag templates. """

  # flags that are always passed to the compiler
  gen: str

  # compile to an executable file with the given name
  # e.g. "/Fe%s" for cl.exe
  exe: str

  # alike exe, but for object files instead
  # e.g. "-c -o %s" for gcc
  obj: str

  # object file extension
  # e.g. "obj" for cl.exe
  obj_ext: str

  # add an include directory
  # e.g. "-I%s" for gcc
  inc: str

  # add a library to link against
  # e.g. "%s.lib" for cl.exe
  #      "-l%s" for gcc
  lib: str

  # pass a flag to the linker, due to the MSVC commandline syntax, the argument
  # this is only really required for compilers with GNU-like commandline syntax
  # e.g. "-Xlinker %s" for gcc
  link: str

  # contains flags specific for C and C++ respecively
  # e.g. "-std=c11" for C via gcc,
  #      "/std:c++17" for C++ via cl.exe
  c: str
  cpp: str

  # flags used for optimized and debug builds respectively
  # e.g. "/DDEBUG /Od" for Debug via cl.exe,
  #      "-DNDEBUG -O3 -flto" for Release via gcc
  opt: str
  dbg: str

  # returns the object filename for the provided source filename
  # e.g. "state.c" -> "state.obj" for cl.exe
  def obj_fn(self, src: str) -> str:
    base, *_ = src.split(".")
    return base+"."+self.obj_ext

  # determines the flags used for the given language based off it's extension
  def lang_flags(self, lang: str) -> str:
    match lang:
      case "c":
        return self.c
      case "cpp":
        return self.cpp
    return ""

  # returns the command for compiling an object file from the given source file
  # with the given include locations
  def for_obj(self, cmd: str, src: Path, out: Path, inc: list[Path], lang: str, debug: bool) -> str:
    return " ".join((
      cmd,
      self.gen,
      self.dbg if debug else self.opt,
      self.lang_flags(lang),
      self.obj % str(out),
      " ".join(self.inc % str(i) for i in inc),
      str(src),
    ))

  # returns the command for compiling an executable file from the given objects,
  # linking aginst the given libraries; the flags returned by the function are
  # ordered in accordance with the cl.exe commandline syntax. gcc-like
  # commandline syntax is position-independent, unlike cl.exe
  def for_exe(self, cmd: str, objs: list[Path], out: Path, lib: list[str], link: list[str], debug: bool) -> str:
    return " ".join((
      cmd,
      self.gen,
      self.dbg if debug else self.opt,
      self.exe % str(out),
      " ".join(str(o) for o in objs),
      " ".join(self.lib % l for l in lib),
      " ".join(self.link % f"{o}" for o in link),
    ))

# flags for compilers with a gcc-like syntax (so gcc and clang)
GNULIKE_FLAGSET = Flagset(
  gen = "-D_CRT_SECURE_NO_WARNINGS",
  exe = "-o %s",
  obj = "-c -o %s",
  obj_ext = "o",
  inc = "-I%s",
  lib = "-l%s",
  c = "-xc -std=c11",
  cpp = "-xc++ -std=c++17",
  opt = "-DNDEBUG -O3 -flto",
  dbg = "-DDEBUG -O0 -Wall -Wpedantic -Wextra",
  link = "-Xlinker %s",
)

# flags for cl.exe
CL_FLAGSET = Flagset(
  gen = "/nologo /D_CRT_SECURE_NO_WARNINGS",
  exe = "/Fe%s",
  obj = "/Fo%s",
  obj_ext = "obj",
  inc = "/I%s",
  lib = "%s.lib",
  c = "/Tc /std:c11",
  cpp = "/Tp /std:c++17",
  opt = "/DNDEBUG /Ot",
  dbg = "/DDEBUG /Od /Wall",
  link = "%s",
)

@dataclass
class Compiler:
  """ Contains information about a C/C++ compiler. """

  # the command used to invoke the compiled
  # e.g. gcc or cl.exe
  cmd: str

  # the flag templates
  flagset: Flagset

  # compiles the given source file into an objec file, returning a tuple
  # containing the resulting object filename and a bool indicating whether the
  # compilation was successful or not
  def compile_obj(self, root: Path, src: Path, out_dir: Path, inc: list[Path], debug: bool, norun: bool) -> tuple[Path, bool]:
    obj = out_dir.joinpath(self.flagset.obj_fn(src.stem))
    if obj.exists() and src.stat().st_mtime < obj.stat().st_mtime:
      return obj, True
    important(f"* {obj.stem}{obj.suffix}")
    lang = src.suffix.removeprefix(".").lower()
    cmd = self.flagset.for_obj(self.cmd, src, obj, inc, lang, debug)
    if norun:
      print(cmd)
      return obj, True
    res = subprocess.run(cmd, shell=True, cwd=root)
    return obj, res.returncode == 0

  # alike compile_obj, compiling multiple object files to a single executable
  # instead. unlike compile_obj, does NOT return the filename of the compiled
  # executable, only the bool signifying success
  def compile_exe(self, root: Path, objs: list[Path], out: Path, lib: list[str], link: list[str], debug: bool, norun: bool = False) -> bool:
    important(f"* {out.stem}{out.suffix}")
    cmd = self.flagset.for_exe(self.cmd, objs, out, lib, link, debug)
    if norun:
      print(cmd)
      return True
    res = subprocess.run(cmd, shell=True, cwd=root)
    return res.returncode == 0

COMPILERS = {
  "clang": Compiler("clang", GNULIKE_FLAGSET),
  "gcc": Compiler("gcc", GNULIKE_FLAGSET),
  "cl": Compiler("cl.exe", CL_FLAGSET),
}

if __name__ == "__main__":
  root = Path(".")
  a = root.joinpath("main.cpp")
  b = root.joinpath("log.c")
  out = root.joinpath("out")
  exe = out.joinpath(exe_name("main"))
  for cname, compiler in COMPILERS.items():
    print(f"  Sample command output for {cname}:")
    objs = []
    obj, ok = compiler.compile_obj(root, a, out, [], False, norun=True)
    objs.append(obj)
    obj, ok = compiler.compile_obj(root, b, out, [], False, norun=True)
    objs.append(obj)
    compiler.compile_exe(root, objs, exe, [], [], False, norun=True)
