import sys
import colorama

def exe_name(fn: str) -> str:
  base, *_ = fn.split(".")
  if sys.platform == "win32":
    return base+".exe"
  return base

def err(msg: str) -> None:
  print(colorama.Fore.RED + msg + colorama.Style.RESET_ALL)

def important(msg: str) -> None:
  print(colorama.Style.BRIGHT + msg + colorama.Style.RESET_ALL)
