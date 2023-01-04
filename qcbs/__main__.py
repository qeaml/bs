import qcbs.job as job
import qcbs.c as c
import qcbs.cli as cli
from qcbs.common import *
import sys
import yaml
import colorama
from pathlib import Path

def main() -> None:
  colorama.just_fix_windows_console()

  args_cmd = cli.Args.parse(sys.argv[1:])

  cmd_project_path = Path(args_cmd.project)
  build_file = cmd_project_path.joinpath("qcbs.yaml")
  args_bf = cli.Args.default()
  if build_file.exists():
    with build_file.open('rt') as f:
      build_info = yaml.load(f, Loader=yaml.Loader)
      if build_info is not None:
        args_bf = cli.Args.from_parsed_dict(build_info)

  args = args_bf.combine(args_cmd)

  if args.exe == "":
    err("Provide an executable name")
    return

  if args.cc == "":
    err("Provide a compiler name")
    return

  project_path = Path(args.project)
  build_file = project_path.joinpath("qcbs.yaml")
  root_path = project_path.joinpath(args.root)
  src_path = project_path.joinpath(args.src)
  bin_path = project_path.joinpath(args.bin)
  obj_path = project_path.joinpath(args.obj)
  incl_paths = [project_path.joinpath(i) for i in args.incl]

  thejob = job.Job(
    root_path, src_path, bin_path, obj_path,
    args.exe, args.cc, args.libs, args.link, incl_paths,
    args.clean, args.debug,
    False
  )

  if args.init:
    cli.init(thejob, project_path, build_file)
  else:
    cli.build(thejob, project_path)

if __name__ == "__main__":
  main()
