import qcbs.job as job
from qcbs.common import *
from pathlib import Path
from dataclasses import dataclass
from typing import Any
from time import time
from datetime import datetime
import subprocess
import sys
import shutil
import os.path

def run_cmd_in(cwd: Path, cmd: str) -> bool:
  return subprocess.run(cmd,
    cwd=cwd,
    shell=True,
    stdout=sys.stderr,
    stderr=sys.stderr).returncode == 0

@dataclass
class Args:
  project: str
  root: str
  src: str
  bin: str
  obj: str

  cc: str
  exe: str
  libs: list[str]
  link: list[str]
  incl: list[Path]

  clean: bool
  debug: bool
  init: bool

  @classmethod
  def parse(cls, args: list[str]) -> "Args":
    pos = []
    named: dict[str, Any] = {}
    for a in args:
      if a.startswith("--"):
        if '=' in a[2:]:
          name, *value_elems = a[2:].split('=')
          named[name] = '='.join(value_elems)
        else:
          named[a[2:]] = True
      else:
        pos.append(a)

    parsed = Args.from_raw_dict(named)

    parsed.project = "."
    if len(pos) > 0:
      parsed.project = pos[0]
    if len(pos) > 1:
      warn("Excess positional arguments ignored.")

    parsed.clean = named.get("clean", False)
    parsed.debug = named.get("debug", False)
    parsed.init = named.get("init", False)

    return parsed

  @classmethod
  def from_raw_dict(cls, data: dict[str, str]) -> "Args":
    project = "."
    root = data.get("root", project)
    src = data.get("src", root)
    bin = data.get("bin", root)
    obj = data.get("obj", bin)
    exe = data.get("exe", "")
    cc = data.get("cc", "")
    libs: list[str] = data.get("lib", "").split(",")
    link: list[str] = data.get("link", "").split(",")
    incl: list[str] = data.get("incl", "").split(",")

    if libs == [""]:
      libs = []
    if link == [""]:
      link = []
    if incl == [""]:
      incl = []

    return cls(
      project, root, src, bin, obj,
      cc, exe, libs, link, [Path(p) for p in incl],
      False, False, False
    )

  @classmethod
  def from_parsed_dict(cls, data: dict[str, Any]) -> "Args":
    project = "."
    root = data.get("root", project)
    src = data.get("src", root)
    bin = data.get("bin", root)
    obj = data.get("obj", bin)
    exe = data.get("exe", "")
    cc = data.get("cc", "")
    libs: list[str] = data.get("lib", [])
    link: list[str] = data.get("link", [])
    incl: list[Path] = data.get("incl", [])

    return cls(
      project, root, src, bin, obj,
      cc, exe, libs, link, incl,
      False, False, False
    )

  @classmethod
  def default(cls) -> "Args":
    project = "."
    return cls(
      project, project, project, project, project,
      "", "", [], [], [],
      False, False, False
    )

  def combine(self, other: "Args") -> "Args":
    defaults = Args.default()
    project = other.project if other.project != self.project and other.project != defaults.project else self.project
    root = other.root if other.root != self.root and other.root != defaults.root else self.root
    src = other.src if other.src != self.src and other.src != defaults.src else self.src
    bin = other.bin if other.bin != self.bin and other.bin != defaults.bin else self.bin
    obj = other.obj if other.obj != self.obj and other.obj != defaults.obj else self.obj
    exe = other.exe if other.exe != self.exe and other.exe != defaults.exe else self.exe
    cc = other.cc if other.cc != self.cc and other.cc != defaults.cc else self.cc
    libs = other.libs if other.libs != self.libs and other.libs != defaults.libs else self.libs
    link = other.link if other.link != self.link and other.link != defaults.link else self.link
    incl = other.incl if other.incl != self.incl and other.incl != defaults.incl else self.incl
    return Args(
      project, root, src, bin, obj,
      cc, exe, libs, link, incl,
      self.clean or other.clean, self.debug or other.debug, self.init or other.init
    )

CLANGD_HEADER = """
CompileFlags:
  Add: [
    -Wall,
    -Wpedantic,
""".strip() + '\n'

CLANGD_FOOTER = """
  ]
---
If:
  PathMatch: .*\\.[ch]
CompileFlags:
  Add: [
    -xc,
    -std=c11,
  ]
---
If:
  PathMatch: .*\\.[ch]pp
CompileFlags:
  Add: [
    -xc++,
    -std=c++17,
  ]
""".strip() + '\n'

def init(j: job.Job, project_path: Path, build_file: Path) -> None:
  start = time()
  important(f"Initializing project at {project_path}")
  if j.clean and project_path.exists():
    important("Replacing old project!")
    shutil.rmtree(project_path)
  project_path.mkdir(parents=True, exist_ok=True)
  j.root.mkdir(parents=True, exist_ok=True)
  important(f"* git init")
  if run_cmd_in(j.root, "git init ."):
    gitignore = j.root.joinpath(".gitignore")
    important(f"* {gitignore}")
    if not gitignore.exists():
      with gitignore.open("xt") as f:
        f.write(f"# automatically generated {datetime.now()}\n")
        if j.bin != j.root:
          f.write(f"{j.bin.relative_to(j.root).as_posix()}\n")
        if j.obj != j.root:
          f.write(f"{j.obj.relative_to(j.root).as_posix()}\n")
  important(f"* {j.src}")
  j.src.mkdir(parents=True, exist_ok=True)
  important(f"* {j.bin}")
  j.bin.mkdir(parents=True, exist_ok=True)
  important(f"* {j.obj}")
  j.obj.mkdir(parents=True, exist_ok=True)

  if j.incl != []:
    for i in j.incl:
      important(f"* {i}")
      i.mkdir(parents=True, exist_ok=True)

  clangd = j.root.joinpath(".clangd")
  clangd_mode = "wt"
  if not clangd.exists():
    clangd_mode = "xt"

  important(f"* {clangd}")
  with clangd.open(clangd_mode) as f:
    f.write(f"# automatically generated {datetime.now()}\n")
    f.write(CLANGD_HEADER)
    for i in j.incl:
      ip = Path(os.path.relpath(i, j.src))
      f.write(f"    -I{ip.as_posix()},\n")
    f.write(CLANGD_FOOTER)

  bf_mode = "wt"
  if not build_file.exists():
    bf_mode = "xt"

  important(f"* {build_file}")
  with build_file.open(bf_mode) as f:
    f.write(f"# automatically generated {datetime.now()}\n")
    f.write(f"cc: '{j.cc.name}'\n")
    f.write(f"exe: '{j.exe}'\n")
    if j.src != j.root:
      f.write(f"src: '{j.src.relative_to(j.root).as_posix()}'\n")
    if j.bin != j.root:
      f.write(f"bin: '{j.bin.relative_to(j.root).as_posix()}'\n")
    if j.obj != j.root and j.obj != j.bin:
      f.write(f"obj: '{j.obj.relative_to(j.root).as_posix()}'\n")
    if j.libs != []:
      f.write("lib:\n")
      for l in j.libs:
        f.write(f"  - '{l}'\n")
    if j.link != []:
      f.write("link:\n")
      for l in j.link:
        f.write(f"  - '{l}'\n")
    if j.incl != []:
      f.write("incl:\n")
      for i in j.incl:
        f.write(f"  - '{i.relative_to(j.root).as_posix()}'\n")

  span = time()-start
  important(f"Finshed in {span:.1f}s")

def build(j: job.Job, project_path: Path) -> None:
  start = time()
  if not project_path.exists():
    err(f"Provided project directory does not exist: {project_path.absolute()}")
    return
  if not j.root.exists():
    err(f"Provided root directory does not exist: {j.root.absolute()}")
    return
  if not j.src.exists():
    err(f"Provided src directory does not exist: {j.src.absolute()}")
    return

  if j.act():
    span = time()-start
    important(f"Successfully built in {span:.1f}s")
