import qcbs.job as job
import qcbs.c as c
from qcbs.common import *
import sys
import yaml
import colorama
from pathlib import Path
from time import time
from dataclasses import dataclass
from typing import Any
from datetime import datetime

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

    project = "."
    if len(pos) > 1:
      project = pos[0]
    if len(pos) > 2:
      warn("Excess positional arguments ignored.")

    parsed = Args.from_raw_dict(named)

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
    project = other.project if other.project != self.project else self.project
    root = other.root if other.root != self.root else self.root
    src = other.src if other.src != self.src else self.src
    bin = other.bin if other.bin != self.bin else self.bin
    obj = other.obj if other.obj != self.obj else self.obj
    exe = other.exe if other.exe != self.exe else self.exe
    cc = other.cc if other.cc != self.cc else self.cc
    libs = other.libs if other.libs != self.libs else self.libs
    link = other.link if other.link != self.link else self.link
    incl = other.incl if other.incl != self.incl else self.incl
    return Args(
      project, root, src, bin, obj,
      cc, exe, libs, link, incl,
      self.debug or other.debug, self.clean or other.clean, self.init or other.init
    )

def main() -> None:
  colorama.just_fix_windows_console()
  start = time()

  args_cmd = Args.parse(sys.argv)
  cmd_project_path = Path(args_cmd.project)
  build_file = cmd_project_path.joinpath("qcbs.yaml")
  args_bf = Args.default()
  if build_file.exists():
    with build_file.open('rt') as f:
      build_info = yaml.load(f, Loader=yaml.Loader)
      if build_info is not None:
        args_bf = Args.from_parsed_dict(build_info)

  args = args_bf.combine(args_cmd)

  if args.exe == "":
    err("Provide an executable name")
    return

  if args.cc == "":
    err("Provide a compiler name")
    return

  if args.init and args.root != args.project:
    args.project = args.root
    args.root = ""

  project_path = Path(args.project)
  build_file = project_path.joinpath("qcbs.yaml")
  root_path = project_path.joinpath(args.root)
  src_path = project_path.joinpath(args.src)
  bin_path = project_path.joinpath(args.bin)
  obj_path = project_path.joinpath(args.obj)
  incl_paths = [project_path.joinpath(i) for i in args.incl]

  if args.init:
    important(f"Initializing project at {root_path}")
    root_path.mkdir(parents=True, exist_ok=True)
    important(f"* {src_path}")
    src_path.mkdir(parents=True, exist_ok=True)
    important(f"* {bin_path}")
    bin_path.mkdir(parents=True, exist_ok=True)
    important(f"* {obj_path}")
    obj_path.mkdir(parents=True, exist_ok=True)

    if args.incl != []:
      for i in args.incl:
        ip = root_path.joinpath(i)
        important(f"* {ip}")
        ip.mkdir(parents=True, exist_ok=True)

    bf_mode = "wt"
    if not build_file.exists():
      bf_mode = "xt"

    important(f"* {build_file}")
    with build_file.open(bf_mode) as f:
      f.write(f"# automatically generated {datetime.now()}\n")
      f.write(f"cc: '{args.cc}'\n")
      f.write(f"exe: '{args.exe}'\n")
      if src_path != root_path:
        f.write(f"src: '{src_path.as_posix()}'\n")
      if bin_path != root_path:
        f.write(f"bin: '{bin_path.as_posix()}'\n")
      if obj_path != root_path:
        f.write(f"obj: '{obj_path.as_posix()}'\n")
      if args.libs != []:
        f.write("libs:\n")
        for l in args.libs:
          f.write(f"  - '{l}'\n")
      if args.link != []:
        f.write("link:\n")
        for l in args.link:
          f.write(f"  - '{l}'\n")
      if args.incl != []:
        f.write("incl:\n")
        for i in args.incl:
          f.write(f"  - '{i.as_posix()}'\n")

    span = time()-start
    important(f"Finshed in {span:.1f}s")
    return

  if not project_path.exists():
    err(f"Provided project directory does not exist: {project_path.absolute()}")
    return
  if not root_path.exists():
    err(f"Provided root directory does not exist: {root_path.absolute()}")
    return
  if not src_path.exists():
    err(f"Provided src directory does not exist: {src_path.absolute()}")
    return

  thejob = job.Job(
    root_path, src_path, bin_path, obj_path,
    args.exe, args.cc, args.libs, args.link, incl_paths,
    args.clean, args.debug,
    False
  )
  if not thejob.act():
    return

  span = time()-start
  important(f"Successfully built in {span:.1f}s")

if __name__ == "__main__":
  main()
