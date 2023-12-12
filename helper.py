"""helper functions"""
# -*- coding: utf8 -*-

from importlib import util
from datetime import datetime
from pathlib import Path
import time
import os

from win32com.client import Dispatch
import psutil
import uiautomation as auto

LOG_LEVELS:tuple = ("ERROR", "INFO", "DEBUG")

def debug(text, level=LOG_LEVELS.index("INFO"), loglevel:int=LOG_LEVELS.index("INFO"), end="\n"):
  """output message depending on log level"""
  if loglevel >= level:
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " - " + text, end=end, flush=True)

def getMaxSize(v1, v2):
  """returns largest value of two parameters"""
  return (v2,v1)[v1 > v2]

def getReadableSize(i) -> str:
  """convert byte to readable size (kB, MB, GB, ...)"""
  for unit in ["", "k", "M", "G", "T"]:
    if abs(i) < 1024.0:
      return f"{i:3.1f}{unit}B"
    i /= 1024.0
  return f"{i:.1f}PB"

def getDirSize(path:str) -> int:
  """return directory recusive size"""

  returnValue = -1

  while returnValue < 0:
    try:
      returnValue = sum(file.stat().st_size for file in Path(path).rglob("*"))
    except FileNotFoundError:
      pass
    except PermissionError:
      pass
    except OSError:
      pass
    else:
      pass

  return returnValue

def isProcessRunning(name:str = "") -> bool:
  """check if process with given name is running"""
  returnValue:bool = False

  for proc in psutil.process_iter():
    try:
      if name.lower() in proc.name().lower():
        returnValue = True
        break
    finally:
      pass

  return returnValue

def getVersion(exe:str):
  """Get version of application from exe"""
  returnValue:str = ""

  if os.path.exists(exe):
    try:
      returnValue = Dispatch("Scripting.FileSystemObject").GetFileVersion(exe)
    finally:
      pass
  return returnValue

def moduleCheck(modules:tuple) -> str:
  """Installed modules check"""
  returnValue:str = ""
  for module in modules:
    if not util.find_spec(module):
      returnValue += f"Module {module} not installed\n"

  return returnValue

def getWindow(ctrl, name) -> auto.Control:
  """get window with windowtext like name"""
  returnValue = None

  if not ctrl is None:
    for item in ctrl.GetChildren():
      if not item is None:
        if not item.GetWindowText() is None:
          if len(item.GetWindowText()) > 0 and name in item.GetWindowText():
            returnValue = item
            break

  return returnValue

def controlExists(ctrl, depth, autoId):
  """check if control exits"""
  if ctrl is None:
    return False

  return ctrl.Control(searchDepth=depth, AutomationId=autoId).Exists(1,1)

def waitForControl(ctrl, depth, autoId, loglevel:int = 1) -> auto.Control:
  """wait for control to exist"""
  returnValue = ctrl.Control(searchDepth=depth, AutomationId=autoId)

  while not returnValue.Exists(1,1):
    returnValue = ctrl.Control(searchDepth=depth, AutomationId=autoId)
    time.sleep(1)

  name:str = ctrl.Control(searchDepth=depth, AutomationId=autoId).Name
  if len(name) > 0:
    name = f" ({name})"
    name = name.replace("\r", "").replace("\n", "")

    if len(name) > 50:
      name = name[:50] + "...)"

  debug("waitForControl = " + autoId + " found" + name, level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)

  return ctrl

def closeBrowserTab(title:str = "", loglevel:int = 1):
  """close opened browser tab with title"""
  if title != "":
    wndBrowser = getWindow(auto.GetRootControl(), title)
    i:int = 0
    while wndBrowser is None and i < 5:
      wndBrowser = getWindow(auto.GetRootControl(), title)
      time.sleep(1)
      i += 1

    if not wndBrowser is None:
      debug("Closing browser window: " + title, level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      wndBrowser.SetFocus()
      wndBrowser.SendKeys("{CTRL}w")
