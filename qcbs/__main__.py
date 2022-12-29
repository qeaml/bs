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
    root = named.get("root", project)
    src = named.get("src", root)
    bin = named.get("bin", root)
    obj = named.get("obj", bin)

    cc = named.get("cc", "")
    exe = named.get("exe", "")
    libs = named.get("libs", "").split(",")
    link = named.get("link", "").split(",")
    incl = named.get("incl", "").split(",")

    if libs == [""]:
      libs = []
    if link == [""]:
      link = []
    if incl == [""]:
      incl = []

    clean = named.get("clean", False)
    debug = named.get("debug", False)

    return cls(
      project, root, src, bin, obj,
      cc, exe, libs, link, incl,
      clean, debug,
    )

def main() -> None:
  colorama.just_fix_windows_console()
  start = time()

  args = Args.parse(sys.argv)
  project_path = Path(args.project)
  if not project_path.exists():
    err(f"Provided project path does not exist: {project_path.absolute()}")
    return

  build_file = project_path.joinpath("qcbs.yaml")
  if not build_file.exists():
    err(f"Build file does not exist: {build_file.absolute()}")
    return

  with build_file.open('rt') as f:
    build_info = yaml.load(f, Loader=yaml.Loader)

    args.root = build_info.get("root", args.root)
    args.src = build_info.get("src", args.src)
    args.bin = build_info.get("bin", args.bin)
    args.obj = build_info.get("obj", args.obj)
    args.exe = build_info.get("exe", args.exe)
    args.cc = build_info.get("cc", args.cc)
    args.libs = build_info.get("libs", args.libs)
    args.link = build_info.get("link", args.link)
    args.incl = build_info.get("incl", args.incl)

  if args.exe == "":
    err("Provide an executable name")
    return

  if args.cc == "":
    err("Provide a compiler name")
    return

  root_path = project_path.joinpath(args.root)
  if not root_path.exists():
    err(f"Provided root directory does not exist: {root_path.absolute()}")
    return
  src_path = project_path.joinpath(args.src)
  if not src_path.exists():
    err(f"Provided src directory does not exist: {src_path.absolute()}")
    return

  bin_path = project_path.joinpath(args.bin)
  obj_path = project_path.joinpath(args.obj)
  incl_paths = [project_path.joinpath(i) for i in args.incl]

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
