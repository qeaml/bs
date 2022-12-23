import qcbs.job as job
import qcbs.c as c
from qcbs.common import *
import sys
import yaml
import colorama
from pathlib import Path
from time import time

def main() -> None:
  colorama.just_fix_windows_console()
  start = time()

  project: Path
  if len(sys.argv) == 1:
    project = Path(".")
  else:
    project = Path(sys.argv[1])

  if not project.exists():
    err(f"Provided project path does not exist: {project.absolute()}")
    return

  root: Path
  src: Path
  bin: Path
  obj: Path
  exe: str
  cc: str
  libs: list[str]
  incl: list[Path]
  clean = "clean" in sys.argv
  debug = "debug" in sys.argv

  build_file = project.joinpath("qcbs.yaml")
  if not build_file.exists():
    err(f"Build file does not exist: {build_file.absolute()}")
    return

  with build_file.open('rt') as f:
    build_info = yaml.load(f, Loader=yaml.Loader)

    if "root" not in build_info:
      root = project
    else:
      root = Path(build_info["root"])
    root = root.resolve()

    if "src" not in build_info:
      src = root
    else:
      src = root.joinpath(root, Path(build_info["src"]))

    if "bin" not in build_info:
      bin = root
    else:
      bin = root.joinpath(root, Path(build_info["bin"]))

    if "obj" not in build_info:
      obj = bin
    else:
      obj = root.joinpath(root, Path(build_info["obj"]))

    if "exe" not in build_info:
      return
    exe = build_info["exe"]

    if "cc" not in build_info:
      return
    cc = build_info["cc"]
    if cc not in c.COMPILERS:
      return

    if "libs" not in build_info:
      libs = []
    else:
      libs = build_info["libs"]

    if "incl" not in build_info:
      incl = []
    else:
      incl = [root.joinpath(Path(i)) for i in build_info["incl"]]

  if not root.exists():
    err(f"Provided root directory does not exist: {root.absolute()}")
    return
  if not src.exists():
    err(f"Provided src directory does not exist: {src.absolute()}")
    return

  thejob = job.Job(root, src, bin, obj, exe, cc, libs, incl, clean, debug, False)
  if thejob.act():
    span = time()-start
    important(f"Successfully built in {span:.1f}s")

if __name__ == "__main__":
  main()
