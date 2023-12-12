"""Automate Axiom processing"""
# -*- coding: utf8 -*-

import sys
import subprocess
import time
import os
from datetime import datetime, timedelta, date
from hashlib import md5
from socket import gethostname
from multiprocessing import cpu_count
import configparser
import argparse

import psutil
import uiautomation as auto
from comtypes import COMError

import helper
from helper import LOG_LEVELS, debug, getWindow, controlExists, closeBrowserTab, waitForControl
import performance

from axiom_db import axiom_db

DEFAULT_LOG_LEVEL:str = "INFO"

scriptversion = "1.0"
version       = "7.7.0.38007" #expected version of application
exe           = "" #executable file of application
case          = "" #case number
image         = "" #image file to process
casefolder    = "" #case folder
tempfolder    = "" #temp folder
waittime:int  = 5 #time to wait before checks och performance output
imagetype:str = "win" #type of image (win, linux, mac)

processtitle = ""
examinetitle = ""

axiomSettings = ""
db:axiom_db = None

loglevel:int = LOG_LEVELS.index(DEFAULT_LOG_LEVEL)

args = None

perf:performance.performance = performance.performance()

def isFinished(filename:str) -> bool:
  """return if process is finish by checking log file"""
  returnValue:bool = False
  lines = []

  if os.path.exists(filename):
    with open(file=filename, mode="r", encoding="utf-8") as reader:
      lines = reader.readlines()

    reader.close()

    for line in reversed(lines):
      if "Search Outcome: " in line:
        returnValue = True
        break

  return returnValue

def getStatistics(filename:str) -> str:
  """return statistics from application log file"""
  returnValue:str = ""
  lines = []

  if os.path.exists(filename):
    with open(file=filename, mode="r", encoding="utf-8") as reader:
      lines = reader.readlines()

    reader.close()

    for line in reversed(lines):
      if " Time: " in line or " Duration: " in line or " Outcome: " in line:
        returnValue = line + returnValue

  return returnValue

def waitForFinish(step:str, func, arguments):
  """Wait until function finish (function returns true)"""

  part:str = ""
  i:int = 1

  if args.perf:
    debug("Wait for finish...", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
  else:
    debug("Wait for finish...", end="", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)

  perf.add(name=step, casefolder=casefolder + "\\" + case, tempfolder=tempfolder)
  time.sleep(waittime)

  while not func(arguments):
    #Move mouse one pixel to stop screensaver/power off display
    auto.SetCursorPos(auto.GetCursorPos()[0],auto.GetCursorPos()[1]+i)
    i = (1,0)[i]

    part = str(perf.add(name=step, casefolder=casefolder + "\\" + case, tempfolder=tempfolder))
    if args.perf:
      debug(part, level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
    else:
      if loglevel >= LOG_LEVELS.index("INFO"):
        print(".", end = "", flush=True)

    time.sleep(waittime)

  if not args.perf and loglevel >= LOG_LEVELS.index("INFO"):
    print("", flush=True)

  #if args.perf:
  #  if loglevel == LOG_LEVELS.index("DEBUG"):
  #    values:str = '\r\n\t'.join(perf.getValues(step))
  #    debug(f"Performance values ({step}):\r\n\t{values}", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)

  debug(f"Finished ({step}) {perf.getMax(step)}", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)

def waitForLogFile(step:str, filename:str):
  """wait for log file and process complete"""

  debug("Wait for log file...", end="", level=LOG_LEVELS.index("INFO"))
  while not os.path.exists(filename):
    time.sleep(waittime)

    if loglevel >= LOG_LEVELS.index("INFO"):
      print(".", end = "", flush=True)

  if loglevel >= LOG_LEVELS.index("INFO"):
    print("", flush=True)

  waitForFinish(step, isFinished, filename)

def processPart():
  """process step from config/ini file"""
  for key in config["steps"]:
    debug(f"ProcessPart Start = {key}", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
    startProcessPart = time.time()
    if key == "start":

      debug("Loading application...", end="", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
      start = time.time()
      subprocess.Popen(exe)

      #Waiting for main window incl exceptions check
      check:bool = False
      while not check:
        try:
          while getWindow(auto.GetRootControl(), processtitle) is None:
            if loglevel >= LOG_LEVELS.index("INFO"):
              print(".", end="", flush=True)
            time.sleep(5)
          check = True
        except LookupError:
          pass
        except COMError:
          pass

        if loglevel >= LOG_LEVELS.index("INFO"):
          print(".", end="", flush=True)
        time.sleep(5)

      wnd = getWindow(auto.GetRootControl(), processtitle)

      check = False
      while not check:
        try:
          while not controlExists(wnd, 3, "CreateNewButton"):
            wnd = getWindow(auto.GetRootControl(), processtitle)

            if loglevel >= LOG_LEVELS.index("INFO"):
              print(".", end="", flush=True)
            time.sleep(5)
          check = True
        except LookupError:
          pass
        except COMError:
          pass

      end = time.time()
      if loglevel >= LOG_LEVELS.index("INFO"):
        print("")

      debug("Application loading time: " + str(int(end - start)) + " seconds", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)

      wnd = getWindow(auto.GetRootControl(), processtitle)
      wnd.SetFocus()

      if getWindow(auto.GetRootControl(), processtitle + "- (Checking License)"):
        if getWindow(wnd, "Activate a license"):
          debug("Error: License/Dongle is missing",LOG_LEVELS.index("ERROR"), loglevel=loglevel)
          exit(2)

      if getWindow(wnd, "Antivirus software detected"):
        debug("Antivirus enabled, turning off...", loglevel=loglevel)
        while not getWindow(wnd, "Antivirus software detected") is None:
          getWindow(wnd, "Antivirus software detected").SetFocus()
          getWindow(wnd, "Antivirus software detected").ButtonControl(searchDepth=1, AutomationId="MessageBoxConfirmButton").Click()
          debug("Antivirus enabled, button clicked", loglevel=loglevel)
          time.sleep(1)

        debug("Antivirus disabled", loglevel=loglevel)

    elif key =="close":

      closeBrowserTab("Getting started with Magnet AXIOM", loglevel)

      #Close application
      debug("Close AXIOM Process (activate license)", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      if not getWindow(auto.GetRootControl(), processtitle) is None:
        if not getWindow(getWindow(auto.GetRootControl(), processtitle), "Activate a license") is None:
          getWindow(getWindow(auto.GetRootControl(), processtitle), "Activate a license").GetWindowPattern().Close()

      debug("Close AXIOM Examine", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      while getWindow(auto.GetRootControl(), examinetitle) is not None:
        getWindow(auto.GetRootControl(), examinetitle).GetWindowPattern().Close()
        time.sleep(10)

      debug("Close AXIOM Process", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      while getWindow(auto.GetRootControl(), processtitle) is not None:
        getWindow(auto.GetRootControl(), processtitle).GetWindowPattern().Close()
        time.sleep(30)

      debug("Close AXIOM Process (taskkill)", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      subprocess.Popen("taskkill /f /im:AxiomProcess.exe", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

      debug("Close AXIOM Examine (taskkill)", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      subprocess.Popen("taskkill /f /im:AxiomExamine.exe", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif key == "process":
      wnd = getWindow(auto.GetRootControl(), processtitle)
      wnd.SetFocus()

      edit:auto.EditControl = None

      waitForControl(wnd, 4, "RecentCasesListOkayButton", loglevel)

      time.sleep(2)

      #Create New Case
      debug("Create New Case", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      waitForControl(wnd, 3, "CreateNewButton", loglevel).ButtonControl(searchDepth=3, AutomationId="CreateNewButton").Click()

      #Case number
      waitForControl(wnd, 4, "CaseNumberTextBox", loglevel)
      edit = wnd.EditControl(searchDepth=4, AutomationId="CaseNumberTextBox")
      edit.GetValuePattern().SetValue(case)

      #Case type
      wnd.ComboBoxControl(searchDepth=4, AutomationId="CaseTypeComboBox").SendKeys("{End}")

      #Folder name
      edit = wnd.EditControl(searchDepth=4, AutomationId="FolderNameTextBox")
      edit.GetValuePattern().SetValue(case)

      #File path
      edit = wnd.EditControl(searchDepth=4, AutomationId="FilePathTextBox")
      edit.GetValuePattern().SetValue(casefolder)

      #Acquire Folder Name
      edit = wnd.EditControl(searchDepth=4, AutomationId="AcquireFolderNameTextBox")
      edit.GetValuePattern().SetValue(case)

      #Acquire File path
      edit = wnd.EditControl(searchDepth=4, AutomationId="AcquireFilePathTextBox")
      edit.GetValuePattern().SetValue(casefolder)

      #Examiner
      edit = wnd.EditControl(searchDepth=6, AutomationId="ExaminerTextBox")
      edit.GetValuePattern().SetValue(os.getlogin())

      #Description
      text:str = ""
      for infoKey, infoValue in getInfo().items():
        text += f"{infoKey}: {infoValue}\n"
      edit = wnd.EditControl(searchDepth=6, AutomationId="DescriptionTextBox")
      edit.GetValuePattern().SetValue(text)
      time.sleep(1)

      #Go to evidence sources
      waitForControl(wnd, 2, "NextButton", loglevel)
      while not wnd.ButtonControl(searchDepth=2, Name="GO TO EVIDENCE SOURCES").Exists(1,1):
        time.sleep(1)
      while wnd.ButtonControl(searchDepth=2, Name="GO TO EVIDENCE SOURCES").Exists(1,1):
        wnd.ButtonControl(searchDepth=2, Name="GO TO EVIDENCE SOURCES").Click()
        time.sleep(1)

      #Computer Evidence Source
      waitForControl(wnd, 6, "ComputerEvidenceSource", loglevel).Control(searchDepth=6, AutomationId="ComputerEvidenceSource").Click()

      if imagetype == "win": #Windows Evidence Source
        waitForControl(wnd, 7, "WindowsEvidenceSource", loglevel).Control(searchDepth=7, AutomationId="WindowsEvidenceSource").GetParentControl().Click()

        #Load Evidence Source
        waitForControl(wnd, 7, "LoadEvidenceSource", loglevel).Control(searchDepth=7, AutomationId="LoadEvidenceSource").GetParentControl().Click()
      elif imagetype == "mac": #Mac Evidence Source"
        waitForControl(wnd, 7, "MacEvidenceSource", loglevel).Control(searchDepth=7, AutomationId="MacEvidenceSource").GetParentControl().Click()
      elif imagetype == "linux": #Linux Evidence Source
        waitForControl(wnd, 7, "LinuxEvidenceSource", loglevel).Control(searchDepth=7, AutomationId="LinuxEvidenceSource").GetParentControl().Click()
      else:
        debug(f"Error, invalid type used ({imagetype})", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
        sys.exit(2)

      #Image Evidence Source
      waitForControl(wnd, 7, "ImageEvidenceSource", loglevel).Control(searchDepth=7, AutomationId="ImageEvidenceSource").GetParentControl().Click()

      #Select image
      debug("Select image", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      wndImage = getWindow(wnd, "Select the image")
      wndImage.SetFocus()

      edit = wndImage.EditControl(searchDepth=4, AutomationId="1148")
      edit.GetValuePattern().SetValue(image)

      while not getWindow(wnd, "Select the image") is None:
        wndImage.Control(searchDepth=1, AutomationId="1").Click()
        time.sleep(1)

      #Check if messagebox about segmented image is displayed (.E01, .E02, ...) and close if exists
      if wnd.Control(1, AutomationId="MessageBox for Segmented image detected").Exists(5,1):
        waitForControl(wnd, 2, "MessageBoxConfirmButton", loglevel).Control(searchDepth=2, AutomationId="MessageBoxConfirmButton").Click()

      #Wait for image analyze + Next
      while not wnd.Control(searchDepth=2, AutomationId="NextButton").IsEnabled:
        time.sleep(1)

      wnd.Control(searchDepth=2, AutomationId="NextButton").Click()

      #Select search type + Next
      while wnd.Control(searchDepth=2, AutomationId="NextButton").Name == "NEXT":
        wnd.Control(searchDepth=2, AutomationId="NextButton").Click()
        time.sleep(1)

      #Go to processing details
      while wnd.Control(searchDepth=2, AutomationId="NextButton").Name == "GO TO PROCESSING DETAILS":
        wnd.ButtonControl(searchDepth=2, Name="GO TO PROCESSING DETAILS").Click()
        time.sleep(1)

      #Processing details
      debug("Processing details", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)

      #Categorize pictures and videos
      debug("Analyze pictures with Magnet.AI", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      wnd.ButtonControl(searchDepth=4, Name="ANALYZE PICTURES WITH MAGNET.AI").SendKeys("{Enter}") #.Click()

      cb:auto.CheckBoxControl = wnd.CheckBoxControl(searchDepth=4, Name="Build picture comparison to enable finding similar pictures in AXIOM Examine")

      if cb.GetTogglePattern().ToggleState == auto.ToggleState.On:
        cb.GetTogglePattern().Toggle()
      cb.GetTogglePattern().Toggle()

      artifacts = wnd.Control(searchDepth=5, AutomationId="ClassifiersDataGrid")

      for item, _ in auto.WalkControl(artifacts, includeTop=False):
        if isinstance(item, auto.CheckBoxControl) and item.IsEnabled:
          wnd.SendKeys("{TAB}" * 5) #Fix because only top datagridrows is accessible
          if item.GetTogglePattern().ToggleState == auto.ToggleState.Off:
            item.GetTogglePattern().Toggle()

      wnd.CaptureToImage(datetime.now().strftime("%Y-%m-%dT%H%M%S") + "_ProcessingDetails.CategorizePicturesAndVideos.png")
      time.sleep(1)

      #OCR
      debug("OCR", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      wnd.TextControl(searchDepth=5, AutomationId="ExtractTextFromFilesViewModelLeftNavItem").Click()
      artifacts = wnd.Control(searchDepth=2, AutomationId="ExtractTextFromFilesSectionViewControl")

      for item, _ in auto.WalkControl(artifacts, includeTop=False):
        if isinstance(item, auto.CheckBoxControl) and item.IsEnabled:
          if item.GetTogglePattern().ToggleState == auto.ToggleState.Off:
            item.GetTogglePattern().Toggle()

      wnd.CaptureToImage(datetime.now().strftime("%Y-%m-%dT%H%M%S") + "_ProcessingDetails.OCR.png")
      time.sleep(1)

      #Chats with Magnet.AI
      debug("Analyze chats with Magnet.AI", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      wnd.TextControl(searchDepth=5, AutomationId="CategorizeChatsLeftNavItem").Click()
      artifacts = wnd.Control(searchDepth=5, AutomationId="ClassifiersDataGrid")

      for item, _ in auto.WalkControl(artifacts, includeTop=False):
        if isinstance(item, auto.CheckBoxControl) and item.IsEnabled:
          if item.GetTogglePattern().ToggleState == auto.ToggleState.Off:
            item.GetTogglePattern().Toggle()

      wnd.CaptureToImage(datetime.now().strftime("%Y-%m-%dT%H%M%S") + "_ProcessingDetails.Chats.png")
      time.sleep(5)

      #Customize computer artifacts
      debug("Customize computer artifacts", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      wnd.TextControl(searchDepth=5, AutomationId="PcArtifactsSelector").GetParentControl().Click()
      time.sleep(2)

      #Clear all + Check all
      wnd.SetFocus()

      while wnd.ButtonControl(searchDepth=3, AutomationId="CheckAllButton").Name == "CLEAR ALL":
        wnd.ButtonControl(searchDepth=3, AutomationId="CheckAllButton").Click()
        time.sleep(1)
      wnd.ButtonControl(searchDepth=3, AutomationId="CheckAllButton").Click()
      wnd.ButtonControl(searchDepth=3, AutomationId="ShowAllButton").Click()
      time.sleep(1)

      wnd.CaptureToImage(datetime.now().strftime("%Y-%m-%dT%H%M%S") + "_ProcessingDetails.ComputerArtifacts.png")
      time.sleep(1)

      artifacts = wnd.Control(searchDepth=4, ClassName="ArtifactItemsView")

      if not wordlist == "": #If wordlist is present add possible passwords to textboxes
        waitForControl(wnd, 3, "ArtifactSelectionScrollViewer", loglevel).Control(3, AutomationId="ArtifactSelectionScrollViewer").SetFocus()
        wnd.SendKeys("{TAB}")

        #Read from wordlist file
        words=""
        encodings:list = ["utf-8", "windows-1250", "windows-1252", "cp850", "ascii"]
        for enc in encodings:
          try:
            with open(wordlist, mode="r", encoding=str(enc)) as reader:
              for line in reader.readlines():
                words += line.rstrip() + "\r\n"
              words = words.rstrip()
          except UnicodeDecodeError:
            pass
          else:
            debug(f"Wordlist encoding = {str(enc)}", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
            break

        if len(words) > 0:
          debug("Wordlist = " + words.replace("\r\n", " "), level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
          for item, _ in auto.WalkControl(artifacts, includeTop=False): #Walk through every artifact
            if isinstance(item, auto.CheckBoxControl) and item.IsEnabled:
              wnd.SendKeys("{TAB}" * 2)
            elif isinstance(item, auto.TextControl):
              if item.Name in ("Apple Keychain", "Apple Notes", "Chrome", "Dropbox", "Edge/Internet Explorer", "Firefox", "Telegram", "WhatsApp", "Windows Stored Credentials", "Zoom"): #Artifacts where passwords should be entered
                if item.IsEnabled:
                  while not wnd.Control(searchDepth=2, AutomationId="cmdPasswordArea").Exists(2,2):
                    item.GetParentControl().Control(searchDepth=1, AutomationId="ArtifactOptionsLabel").Click(x=-125, y=-15)

                  debug("Artifact = " + item.Name + " (set password)", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
                  waitForControl(wnd, 2, "cmdPasswordArea", loglevel).EditControl(2, AutomationId="cmdPasswordArea").GetValuePattern().SetValue(words)

                  while wnd.Control(searchDepth=2, AutomationId="cmdPasswordArea").Exists(1,1):
                    waitForControl(wnd, 2, "cmdYes", loglevel).ButtonControl(2, AutomationId="cmdYes").Click()
                    if wnd.Control(searchDepth=3, AutomationId="6").Exists(5,1):
                      waitForControl(wnd, 3, "6", loglevel).ButtonControl(3, AutomationId="6").Click()

                  if item.GetParentControl().GetTogglePattern().ToggleState == auto.ToggleState.Off:
                    item.GetParentControl().GetTogglePattern().Toggle()

                  item.SetFocus()

      #Print enabled/disabled artifacts
      if loglevel >= LOG_LEVELS.index("DEBUG"):
        enabledArtifacts:list = []
        disabledArtifacts:list = []

        for item, _ in auto.WalkControl(artifacts, includeTop=False):
          if isinstance(item, auto.CheckBoxControl):
            (disabledArtifacts, enabledArtifacts)[item.GetTogglePattern().ToggleState].append(item.Control(searchDepth=1, AutomationId="ArtifactNameLabel").Name)

        debug("Enabled artifacts = " + ", ".join(enabledArtifacts), level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
        debug("Disabled artifacts = " + ", ".join(disabledArtifacts), level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)

      #Go to analyze evidence
      debug("Go to analyze evidence", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      while not wnd.Control(searchDepth=2, AutomationId="NextButton").Name == "GO TO PARSE AND CARVE ARTIFACTS":
        time.sleep(1)
        debug("NextButton = " + wnd.Control(searchDepth=2, AutomationId="NextButton").Name + " (GO TO PARSE AND CARVE ARTIFACTS)", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      while not wnd.Control(searchDepth=2, AutomationId="NextButton").Name == "GO TO ANALYZE EVIDENCE":
        wnd.ButtonControl(searchDepth=2, AutomationId="NextButton").Click()
        time.sleep(1)
        debug("NextButton = " + wnd.Control(searchDepth=2, AutomationId="NextButton").Name + " (GO TO ANALYZE EVIDENCE)", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)

      #Analyze evidence
      debug("Analyze evidence", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
      check = False
      while not check:
        try:
          while not wnd.Control(searchDepth=2, AutomationId="NextButton").Name == "ANALYZE EVIDENCE":
            time.sleep(1)
            debug("NextButton = " + wnd.Control(searchDepth=2, AutomationId="NextButton").Name + " (ANALYZE EVIDENCE)", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
            wnd.ButtonControl(searchDepth=2, AutomationId="NextButton").Click()
          check = True
        finally:
          pass

        debug("Check/NextButton = " + wnd.Control(searchDepth=2, AutomationId="NextButton").Name, level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)
        time.sleep(1)

      wnd.ButtonControl(searchDepth=2, AutomationId="NextButton").Click()

      waitForLogFile(key, casefolder + "\\" + case + "\\Case Information.txt")

      if loglevel >= LOG_LEVELS.index("INFO"):
        debug("-" * 100, level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
        print(getStatistics(casefolder + "\\" + case + "\\Case Information.txt").rstrip("\n"))
        debug("-" * 100, level=LOG_LEVELS.index("INFO"), loglevel=loglevel)

      #Wait for Examine
      debug("Wait for Examine...", end="", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
      check = False
      while not check:
        try:
          while getWindow(auto.GetRootControl(), examinetitle) is None:
            if loglevel >= LOG_LEVELS.index("INFO"):
              print(".", end="", flush=True)
            time.sleep(5)

          check = True
        finally:
          pass

        if loglevel >= LOG_LEVELS.index("INFO"):
          print(".", end="", flush=True)
          time.sleep(5)

      if loglevel >= LOG_LEVELS.index("INFO"):
        print("", flush=True)

      #Wait for processing evidence
      wnd = getWindow(auto.GetRootControl(), examinetitle)
      waitForControl(wnd, 4, "ProgressControl", loglevel)

      debug("Wait for picture comparison...", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
      waitForFinish(key, wnd.Control(searchDepth=4, Name="Building picture comparison completed").Exists,1)

      #debug("Wait for picture categorization...", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
      #waitForFinish(key, wnd.Control(searchDepth=4, Name="Finished picture categorization").Exists,1)

      while controlExists(wnd, 5, "DismissProgressItem"):
        wnd.SetFocus()
        waitForControl(wnd, 5, "DismissProgressItem", loglevel).Control(5, AutomationId="DismissProgressItem").Click()

      #Load new evidence
      if controlExists(wnd, 4, "CaseGenerationStatusAction"):
        while wnd.Control(searchDepth=4, AutomationId="CaseGenerationStatusAction").GetLegacyIAccessiblePattern().State == 0:
          wnd.SetFocus()
          waitForControl(wnd, 4, "CaseGenerationStatusAction", loglevel).Control(4, AutomationId="CaseGenerationStatusAction").Click()

      #Print information from Case DB
      caseDB = axiom_db(casefolder + "\\" + case + "\\Case.mfdb", loglevel)
      if caseDB.connectRAM():
        if caseDB.isConnected():
          debug(caseDB.getCaseInfo("filesystem"), level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
          debug(caseDB.getCaseInfo("os"), level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
        caseDB.close()

    elif key == "portablecase": #Create portable case
      wnd = getWindow(auto.GetRootControl(), examinetitle)
      while not controlExists(wnd, 3, "ExportWizardNextButton"):
        try:
          wnd.SetFocus()
          wnd.SendKey("{ESC}")
          time.sleep(1)
          wnd.MenuItemControl(Name = "File").Click()
          time.sleep(1)
          if wnd.MenuItemControl(Name = "Create portable case").IsEnabled:
            wnd.MenuItemControl(Name = "Create portable case").Click()
        except LookupError:
          pass
        except COMError:
          pass

      while not wnd.RadioButtonControl(7, Name="All evidence").Exists(1,1):
        waitForControl(wnd, 3, "ExportWizardNextButton", loglevel).ButtonControl(3, AutomationId="ExportWizardNextButton").Click()
        time.sleep(1)
      wnd.RadioButtonControl(7, Name="All evidence").Click() #Items to include

      while controlExists(wnd, 3, "ExportWizardNextButton"):
        waitForControl(wnd, 3, "ExportWizardNextButton", loglevel).ButtonControl(3, AutomationId="ExportWizardNextButton").Click()
        time.sleep(1)

      debug("Wait for portable case...", end="", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
      while wnd.Control(searchDepth=4, Name="Exporting to portable case...").Exists(1,1):
        time.sleep(5)
        if loglevel >= LOG_LEVELS.index("INFO"):
          print(".", end = "", flush=True)

      while not wnd.Control(searchDepth=4, Name="Export to portable case complete.").Exists(1,1):
        time.sleep(5)
        if loglevel >= LOG_LEVELS.index("INFO"):
          print(".", end = "", flush=True)

      if loglevel >= LOG_LEVELS.index("INFO"):
        print("", flush=True)

      wnd.SetFocus()
      waitForControl(wnd, 5, "DismissProgressItem", loglevel).Control(5, AutomationId="DismissProgressItem").Click()

      closeBrowserTab("Getting started with Magnet AXIOM", loglevel)

    timeProcessPart = str(timedelta(seconds=time.time() - startProcessPart)).split(".", maxsplit=1)[0]
    debug(f"ProcessPart Finish = {key} ({timeProcessPart})", level=LOG_LEVELS.index("DEBUG"), loglevel=loglevel)

def getInfo() -> dict:
  """return common info about script, computer and parameters"""

  if args.threads:
    threadsValue = args.threads
  else:
    threadsValue = db.getValue("Threads")

  return {
    "Command line": " ".join(sys.argv),
    "Command MD5": md5(open(sys.argv[0],"rb").read()).hexdigest(),
    "Script ver": scriptversion,
    "Computer name": gethostname(),
    "CPU Cores": cpu_count(),
    "Threads": threadsValue,
    "RAM": str(helper.getReadableSize(psutil.virtual_memory().total)) + " (current usage: " + str(helper.getReadableSize(psutil.virtual_memory().used)) + ")",
    "Application":  exe + " (" + helper.getVersion(exe) + ")",
    "Settings": axiomSettings + " (" + settings_from + ")",
    "Process title":  processtitle,
    "Examine title":  examinetitle,
    "Case name": case,
    "Image": image + " (" + helper.getReadableSize(os.path.getsize(image)) + ")",
    "Wordlist": wordlist,
    "Image type": imagetype,
    "Case folder": casefolder,
    "Temp folder": tempfolder,
    "Wait time": str(waittime)
  }

def main():
  """main application"""
  for key, value in info.items():
    debug(f"{key:14}= {value}", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)

  debug("-" * 100, level=LOG_LEVELS.index("INFO"), loglevel=loglevel)

  if args.threads:
    if int(args.threads) != int(db.getValue("Threads")):
      db.setValue("Threads", (args.threads, ))
      db.setValue("SearchSpeed", (args.threads, ))

  if tempfolder != db.getValue("TempFolder"):
    db.setValue("TempFolder", (tempfolder, ))

  if db.getValue("QuickTips") != "False":
    db.setValue("QuickTips")

  if db.getValue("LastDateOnline") != str(date.today()):
    db.setValue("LastDateOnline",(str(date.today()),))

  if db.getValue("AutoCheckUpdates") != "False":
    db.setValue("AutoCheckUpdates")

  if db.getValue("Telemetry") != "False":
    db.setValue("Telemetry")

  db.close()

  debug("Process Start", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
  startProcess = time.time()

  processPart()

  timeProcess = str(timedelta(seconds=time.time() - startProcess)).split(".", maxsplit=1)[0]
  debug(f"Process Finish ({timeProcess})", level=LOG_LEVELS.index("INFO"), loglevel=loglevel)

  #if args.perf:
  debug(perf.getMax(), level=LOG_LEVELS.index("INFO"), loglevel=loglevel)
  debug("-" * 100, level=LOG_LEVELS.index("INFO"), loglevel=loglevel)

#prechecks, arguments and read config values from ini
if __name__ == "__main__":

  if not auto.IsUserAnAdmin():
    auto.RunScriptAsAdmin(sys.argv)
  else:

    config = configparser.ConfigParser(allow_no_value=True)
    configEnv = configparser.ConfigParser(os.environ, allow_no_value=True) #With env variables
    config.read("axiom.ini")
    configEnv.read("axiom.ini")

    exe = config["default"]["Execute"]
    waittime = int(config["default"]["WaitTime"])
    DEFAULT_LOG_LEVEL = config["default"]["LogLevel"]

    processtitle = config["default"]["ProcessTitle"] + " " + version
    examinetitle = config["default"]["ExamineTitle"] + version

    if not os.path.exists(exe):
      debug(f"Error, executable \"{exe}\" doesn't exist", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    if version != helper.getVersion(exe):
      debug("Error, Axiom " + helper.getVersion(exe) + " installed at " + exe + ", expecting " + version, level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", type = str, help = "case name", required=True)
    parser.add_argument("-i", "--img", type = str, help = "image file", required=True)
    parser.add_argument("-p", "--path", type = str, help = "case folder path", required=True)
    parser.add_argument("-w", "--wordlist", type = str, help = "wordlist file with passwords", default="")
    parser.add_argument("-t", "--threads", type = int, help="set processing threads count")
    parser.add_argument("--type", type = str, default = "win", help="image type (win, mac, linux)")
    parser.add_argument("--temp", type = str, help="temp folder path")
    parser.add_argument("--perf", action = "store_true", help = "show performance info")
    parser.add_argument("--checkdb", action = "store_true", help = "show settings database values")
    parser.add_argument("-v", "--verbose", action = "count", default = LOG_LEVELS.index(DEFAULT_LOG_LEVEL), help = "more verbose output")
    args = parser.parse_args()

    case = args.name
    image = args.img
    casefolder = args.path
    tempfolder = args.temp
    loglevel = args.verbose
    imagetype = args.type.lower()
    wordlist = args.wordlist

    settings_from:str = ""

    if os.path.exists(configEnv["default"]["Settings"]):
      axiomSettings = configEnv["default"]["Settings"]
      settings_from = "axiom.ini"
    else:
      if os.path.exists("C:\\Users\\" + os.getlogin() + "\\AppData\\Local\\Axiom Examine\\Settings.db"):
        axiomSettings = "C:\\Users\\" + os.getlogin() + "\\AppData\\Local\\Axiom Examine\\Settings.db"
        settings_from = "os.getlogin()"

    if not os.path.exists(axiomSettings):
      debug(f"Error, settings file \"{axiomSettings}\" doesn't exist", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    db = axiom_db(axiomSettings, loglevel)

    if not db.connect() or not db.isConnected():
      debug("Error, couldn't connect to Axiom settings database (" + axiomSettings  + ")", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      exit(1)

    if args.checkdb:
      print(db, end="")
      db.close()
      sys.exit(0)

    if not tempfolder:
      tempfolder = casefolder

    info:dict = getInfo()

    if not loglevel == LOG_LEVELS.index(DEFAULT_LOG_LEVEL):
      if loglevel > len(LOG_LEVELS) - 1:
        loglevel = len(LOG_LEVELS) - 1
      info["Verbose"] = str(LOG_LEVELS[loglevel])

    if not os.path.exists(tempfolder):
      debug(f"Error, temp folder \"{tempfolder}\" doesn't exist", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    if not os.path.exists(image):
      debug(f"Error, image file \"{image}\" doesn't exist", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    if not os.path.exists(casefolder):
      debug(f"Error, case path \"{casefolder}\" doesn't exist", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    if os.path.exists(casefolder + "\\" + case):
      debug(f"Error, case path \"{casefolder}\\{case}\" already exist", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    if helper.isProcessRunning("AxiomProcess.exe"):
      debug("Error, AxiomProcess.exe is already running", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    if helper.isProcessRunning("AxiomExamine.exe"):
      debug("Error, AxiomExamine.exe is already running", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    if not imagetype in ["win", "mac", "linux"]:
      debug(f"Error, invalid type used ({imagetype}). Expecting win, mac or linux.", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    if not os.path.exists(wordlist) and not wordlist == "":
      debug(f"Error, wordlist file \"{wordlist}\" doesn't exist", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    if not str(args.threads).isdigit() and not args.threads is None:
      debug(f"Error, threads ({args.threads}) is not digits", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
      sys.exit(1)

    if not args.threads is None:
      if  (int(args.threads) < 1 or int(args.threads) > 32):
        debug("Error, threads is not between 1 and 32", level=LOG_LEVELS.index("ERROR"), loglevel=loglevel)
        sys.exit(1)

    try:
      main()
    except KeyboardInterrupt:
      pass
