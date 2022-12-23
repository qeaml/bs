from qcbs.common import *
from pathlib import Path
import shutil
import qcbs.c as c

SOURCE_FILE_EXTS = ["c", "cpp"]

class Job:
  """ Represents a compilation job. """

  # the root of the compilation, usually the project directory
  # e.g. "/user/Timmy/projects/my-app"
  #      "C:\Projects\C\MyApp"
  root: Path

  # where the source files are loacted, in relation to the root directory
  # e.g. "src", "source"
  src: Path

  # where the final executables will end up, relative to root
  # e.g. "bin", "build", "out", "target"
  bin: Path

  # where object files will end up, relative to root
  # e.g. "obj", "comp"
  obj: Path

  # name of the final executable, excluding extension, relative to bin
  # e.g. "my-app"
  exe: str

  # the C/C++ compiler to use, has to be present in c.COMPILERS
  # e.g. "gcc"
  cc: c.Compiler

  # libs to link against for the final executable
  # e.g. ["SDL2", "SDL2_main"]
  libs: list[str]

  # directories to include during compilation, relative to src
  # e.g. ["imgui"]
  incl: list[Path]

  # whether to clean bin before building
  clean: bool

  # whether to build with debug flags
  debug: bool

  # whether to just print the commands as opposed to running them
  norun: bool

  # discovered source files
  sources: list[Path]

  # available object files
  #   a) already compiled from previous builds
  #   b) newly compiled by this build
  objects: list[Path]

  def __init__(self, root: Path, src: Path, bin: Path, obj: Path, exe: str, cc: str, libs: list[str], incl: list[Path], clean: bool, debug: bool, norun: bool):
    self.root = root
    self.src = src
    self.bin = bin
    self.obj = obj
    self.exe = exe
    self.cc = c.COMPILERS[cc]
    self.libs = libs
    self.incl = incl
    self.clean = clean
    self.debug = debug
    self.norun = norun

    if clean:
      try:
        shutil.rmtree(obj)
        shutil.rmtree(bin)
      except:
        pass

    self.bin.mkdir(exist_ok=True)
    self.obj.mkdir(exist_ok=True)

    self.sources = []
    self.objects = []

  def discover_sources(self) -> None:
    for f in self.src.rglob("*"):
      if f.suffix.removeprefix(".") not in SOURCE_FILE_EXTS:
        continue
      self.sources.append(f)

  def compile_all_objects(self) -> bool:
    for src in self.sources:
      obj, ok = self.cc.compile_obj(self.root, src, self.obj, self.incl, self.debug, norun=self.norun)
      if not ok:
        err("Compilation failed. Aborting.")
        return False
      self.objects.append(obj)
    return True

  def compile_exe(self) -> bool:
    exe = self.bin.joinpath(exe_name(self.exe))
    ok = self.cc.compile_exe(self.root, self.objects, exe, self.libs, self.debug, norun=self.norun)
    if not ok:
      err("Compilation failed. Aborting.")
    return ok

  def act(self) -> bool:
    self.discover_sources()

    if self.clean:
      important("Clean Build!")
      try:
        shutil.rmtree(self.bin)
      except Exception as e:
        err(f"Could not clean: {e.__class__.__name__}: {e}")
        return False
    self.bin.mkdir(exist_ok=True)
    self.obj.mkdir(exist_ok=True)

    ok = self.compile_all_objects()
    if not ok:
      return False

    return self.compile_exe()

if __name__ == "__main__":
  root = Path(".")
  src = root.joinpath("src")
  bin = root.joinpath("bin")
  obj = bin.joinpath("obj")
  exe = "my-app"
  cc = "cl"
  libs = ["SDL2", "SDL2main"]
  incl: list[Path] = []
  job = Job(
    root,
    src,
    bin,
    obj,
    exe,
    cc,
    libs,
    incl,
    True,
    False,
    True,
  )
  job.act()
