"""
db functions
"""
# -*- coding: utf8 -*-

import os
import sqlite3

class db:
  """
  connect to sqlite3 database
  """

  def __init__(self, filename):
    """set filename and make non-connected connection"""
    self.filename:str = filename
    self.db:sqlite3.Connection = None

  def connect(self) -> bool:
    """connect to database"""
    returnValue:bool = False

    try:
      if os.path.exists(self.filename):
        self.db = sqlite3.connect(self.filename)
        returnValue = self.isConnected()
    except sqlite3.Error as err:
      print(f"SQL error: {' '.join(err.args)}")

    return returnValue

  def connectRAM(self) -> bool:
    """connect to database and copy to ram"""
    returnValue:bool = False

    try:
      if os.path.exists(self.filename):

        source = sqlite3.connect(self.filename)
        self.db = sqlite3.connect(":memory:")
        source.backup(self.db)
        source.close()

        returnValue = self.isConnected()
    except sqlite3.Error as err:
      print(f"SQL error: {' '.join(err.args)}")
    else:
      pass

    return returnValue

  def close(self) -> bool:
    """close database onnection"""
    returnValue:bool = False

    try:
      if self.isConnected():
        self.db.close()
        returnValue = True
    except sqlite3.Error as err:
      print(f"SQL error: {' '.join(err.args)}")
    else:
      pass

    return returnValue

  def isConnected(self) -> bool:
    """return connected status"""
    returnValue:bool = False

    if not self.db is None:
      try:
        self.db.cursor()
        returnValue = True
      except sqlite3.Error as err:
        print(f"SQL error: {' '.join(err.args)}")
      else:
        pass

    return returnValue

  def execute(self, sql:str, args:tuple = ()) -> bool:
    """execute command (INSERT/UPDATE/DELETE)"""
    returnValue:bool = False

    try:
      cursor:sqlite3.Cursor = self.db.cursor()
      cursor.execute(sql,  args)
      self.db.commit()
      returnValue = True
    except sqlite3.Error as err:
      print(f"SQL error: {' '.join(err.args)}")
    else:
      pass

    return returnValue

  def fetchone(self, sql:str, args:tuple = ()):
    """fetch one value from database"""
    returnValue = None

    try:
      cursor:sqlite3.Cursor = self.db.cursor()
      cursor.execute(sql,  args)
      returnValue = cursor.fetchone()
      if not returnValue is None:
        returnValue = returnValue[0]
    except sqlite3.Error as err:
      print(f"SQL error: {' '.join(err.args)}")
    else:
      pass

    return returnValue

  def fetchall(self, sql:str, args:tuple = ()) -> list:
    """fetch values from database"""
    returnValue:list = []

    try:
      cursor:sqlite3.Cursor = self.db.cursor()
      cursor.execute(sql,  args)
      returnValue = cursor.fetchall()
    except sqlite3.Error as err:
      print(f"SQL error: {' '.join(err.args)}")
    else:
      pass

    return returnValue
