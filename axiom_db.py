"""
db functions for axiom
"""
# -*- coding: utf8 -*-

import sqlite3
from db import db
from helper import debug, LOG_LEVELS, getReadableSize

class axiom_db(db):
  """db functions for axiom"""
  loglevel:int = 1

  """select values from database"""
  getValueSQL:dict = {
    "Threads": "SELECT setting_value FROM application_setting WHERE setting_name = 'SearchSpeed';",
    "TempFolder": "SELECT setting_value FROM application_setting WHERE setting_name = 'TempFileLocation';",
    "QuickTips": "SELECT setting_value FROM application_setting WHERE setting_name = 'ShowQuickTips';",
    "LastDateOnline": "SELECT setting_value FROM application_setting WHERE setting_name = 'LastDateOnline';",
    "AutoCheckUpdates": "SELECT setting_value FROM application_setting WHERE setting_name = 'AutoCheckUpdates';",
    "Telemetry": "SELECT setting_value FROM application_setting WHERE setting_name = 'CaptureTelemetry';"
  }

  """modify/update values in database"""
  setValueSQL:dict = {
    "Threads": "UPDATE Settings SET Value=? WHERE Setting = 'PreferredNumberOfThreads';",
    "SearchSpeed": "UPDATE application_setting SET setting_value=? WHERE setting_name = 'SearchSpeed';",
    "TempFolder": "UPDATE application_setting SET setting_value=? WHERE setting_name = 'TempFileLocation';",
    "QuickTips": "UPDATE application_setting SET setting_value = 'False' WHERE setting_name = 'ShowQuickTips';",
    "LastDateOnline": "UPDATE application_setting SET setting_value=? WHERE setting_name = 'LastDateOnline';",
    "AutoCheckUpdates": "UPDATE application_setting SET setting_value = 'False' WHERE setting_name = 'AutoCheckUpdates';",
    "Telemetry": "UPDATE application_setting SET setting_value = 'False' WHERE setting_name = 'CaptureTelemetry';"
  }

  """insert values in database"""
  insertValueSQL:dict = {
    "TempFolder": "INSERT INTO application_setting(application_setting_id,setting_name,setting_value) VALUES (lower(hex(randomblob(16))),'TempFileLocation','');",
    "QuickTips": "INSERT INTO application_setting(application_setting_id,setting_name,setting_value) VALUES (lower(hex(randomblob(16))),'ShowQuickTips','False');",
    "LastDateOnline": "INSERT INTO application_setting(application_setting_id,setting_name,setting_value) VALUES (lower(hex(randomblob(16))),'LastDateOnline',date(now));",
    "AutoCheckUpdates": "INSERT INTO application_setting(application_setting_id,setting_name,setting_value) VALUES (lower(hex(randomblob(16))),'AutoCheckUpdates','False');",
    "Telemetry": "INSERT INTO application_setting(application_setting_id,setting_name,setting_value) VALUES (lower(hex(randomblob(16))),'CaptureTelemetry','False');"
  }

  """get values from case database"""
  infoValueSQL:dict = {
    "filesystem": """
      SELECT hit_id, name, value, data_type 
        FROM hit_fragment hf 
          INNER JOIN fragment_definition fd ON hf.fragment_definition_id = fd.fragment_definition_id 
        WHERE artifact_version_id IN (
          SELECT artifact_version_id 
            FROM artifact_version 
            WHERE artifact_id in (
              SELECT artifact_id 
                FROM artifact 
                WHERE artifact_name = \"File System Information\"
            )
        )
          AND name in ("ID", "Volume Serial Number", "Full Volume Serial Number", "File System", "Total Capacity (Bytes)", "Allocated Area (Bytes)")
        ORDER BY hit_id, sort_order;""",

    "os": """
      SELECT hit_id, name, value, data_type 
        FROM hit_fragment hf 
          INNER JOIN fragment_definition fd on hf.fragment_definition_id = fd.fragment_definition_id 
        WHERE artifact_version_id IN (
          SELECT artifact_version_id 
            FROM artifact_version 
            WHERE artifact_id IN (
              SELECT artifact_id 
                FROM artifact 
                WHERE artifact_name LIKE \"Operating%\"
            )
        )
        ORDER BY hit_id, sort_order;"""
  }

  def __init__(self, filename:str = "", loglevel:int = 1):
    """init parent class and set loglevel"""
    super().__init__(filename)
    self.loglevel = loglevel

  def __str__(self):
    """return all stored keys and values"""

    returnValue = ""

    if not self.db is None:
      if self.isConnected():
        for key, _ in self.getValueSQL.items():
          returnValue += f"{key}: {self.getValue(key)}\n"

    if len(returnValue) > 0:
      returnValue = returnValue[:-1]

    return returnValue

  def getValue(self, key:str) -> str:
    """get value from db"""

    returnValue:str = None

    try:
      if self.isConnected():
        returnValue = self.fetchone(self.getValueSQL[key])
        if returnValue is None and self.insertValueSQL.get(key) is not None:
          self.execute(self.insertValueSQL[key])
          returnValue = ""
          debug(f"axiom_db, getValue({key}) not found --> inserted", level=LOG_LEVELS.index("DEBUG"), loglevel=self.loglevel)

    except sqlite3.Error as err:
      print(f"SQL error: {' '.join(err.args)}")
    else:
      pass

    return returnValue

  def setValue(self, key:str, value:tuple = ()) -> bool:
    """set value in db"""
    returnValue:bool = False

    try:
      if self.isConnected():
        self.execute(self.setValueSQL[key], value)
        returnValue = True
        debug(f"axiom_db, setValue({key}, {value})", level=LOG_LEVELS.index("DEBUG"), loglevel=self.loglevel)
    except sqlite3.Error as err:
      print(f"SQL error: {' '.join(err.args)}")
    else:
      pass

    return returnValue

  def getCaseInfo(self, key:str) -> str:
    """get information from case database"""
    returnValue:str = ""
    hit_id:int = -1
    indent:str = ""

    for row in self.fetchall(self.infoValueSQL[key], ()):
      indent = ("[+] ", "    ")[int(row[0]) == hit_id]
      hit_id = int(row[0])
      if len(str(row[1])) > 0:
        if " (Bytes)" in str(row[1]) and str(row[2]).isdigit():
          returnValue += indent + str(row[1]) + ": " + str(getReadableSize(int(row[2]))) + "\n"
        else:
          returnValue += indent + str(row[1]) + ": " + str(row[2]) + "\n"

    if len(returnValue) > 0:
      returnValue = returnValue[:-1]

    return "Case information from DB (" + key + ")\n" + returnValue
