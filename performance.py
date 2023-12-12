"""
performance functions
"""
# -*- coding: utf8 -*-
from datetime import datetime
import psutil
import helper

class performance:
  """
  store performance log
  """

  class part():
    """performance part"""

    timestamp = None
    name = ""
    cpu = 0
    ram = 0
    network = 0
    casefolder = 0
    tempfolder = 0

    def __init__(self, *, timestamp, name, cpu, ram, network, casefolder, tempfolder):
      """init performance part"""
      self.timestamp = timestamp
      self.name = name
      self.cpu = cpu
      self.ram = ram
      self.network = network
      self.casefolder = casefolder
      self.tempfolder = tempfolder

    def __str__(self):
      perfInfo = {
        #"Timestamp": f"{self.timestamp}",
        "CPU": f"{self.cpu}%",
        "RAM": helper.getReadableSize(self.ram),
        "Network": helper.getReadableSize(self.network),
        "CaseFolder": helper.getReadableSize(self.casefolder),
        "TempFolder": helper.getReadableSize(self.tempfolder)
        }
      return ", ".join([f"{key}={value}" for key,value in perfInfo.items()])

    def getName(self):
      """return name"""
      return self.name

  parts:list = []
  casefolder:str = ""
  tempfolder:str = ""
  network:int = 0
  timestamp:datetime = None

  def __init__(self):
    """init"""
    self.network = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
    self.timestamp = datetime.now()

  def add(self, *, name, casefolder="", tempfolder="") -> str:
    """set performance values"""

    network=psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
    timestamp:datetime = datetime.now()

    self.parts.append(self.part(
      timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      name=name,
      cpu=psutil.cpu_percent(),
      ram=psutil.virtual_memory().used,
      network=(network - self.network)/(timestamp - self.timestamp).total_seconds(),
      casefolder=helper.getDirSize(casefolder),
      tempfolder=helper.getDirSize(tempfolder)))

    self.network = network
    self.timestamp = timestamp
    return self.parts[len(self.parts)-1]

  def getFilteredList(self, name=None) -> list:
    """Return filtered by name list"""
    returnValue:list = self.parts

    if not name is None:
      returnValue = filter(lambda a: a.name == name, self.parts)

    return returnValue

  def getNames(self):
    """return list with all names"""
    returnValue:list = []
    for part in self.parts:
      if not part.name in returnValue:
        returnValue.append(part.name)
    return returnValue

  def getValues(self, name:str = None, key:str = None) -> list:
    """returns values"""
    returnValue:list = []
    for part in self.getFilteredList(name):
      if not key is None:
        returnValue.append(getattr(part, key))
      else:
        returnValue.append(str(part))
    return returnValue

  def getMax(self, name=None) -> str:
    """returns total max performance values"""
    returnValue:str = ""

    returnValue += f'{"CPU"}={max(self.getValues(name, "cpu"))}%, '

    for item in ("RAM", "Network", "CaseFolder", "TempFolder"):
      returnValue += f'{item}={helper.getReadableSize(max(self.getValues(name, item.lower())))}, '

    return returnValue[:-2]
