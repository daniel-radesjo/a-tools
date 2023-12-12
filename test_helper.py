"""test helper functions"""
# -*- coding: utf8 -*-

import unittest
import os

import uiautomation as auto

import helper

class testHelperFunctions(unittest.TestCase):
  """test helper functions"""

  def test_getMaxSize(self):
    """test getMaxSize"""
    self.assertEqual(helper.getMaxSize(0,1), 1)
    self.assertEqual(helper.getMaxSize(1,1), 1)
    self.assertEqual(helper.getMaxSize(1,0), 1)
    self.assertEqual(helper.getMaxSize(0,0), 0)

    self.assertEqual(helper.getMaxSize("0","1"), "1")
    self.assertEqual(helper.getMaxSize("1","0"), "1")

  def test_getReadableSize(self):
    """test getReadableSize"""
    self.assertEqual(helper.getReadableSize(0), "0.0B")
    self.assertEqual(helper.getReadableSize(1024), "1.0kB")

  def test_getDirSize(self):
    """test getDirSize"""
    self.assertEqual(helper.getDirSize("test_getDirSize"), 0)
    os.mkdir("test_getDirSize")
    self.assertEqual(helper.getDirSize("test_getDirSize"), 0)
    os.rmdir("test_getDirSize")
    self.assertGreater(helper.getDirSize(os.path.join(os.environ["WINDIR"],"Tasks")), 0)

  def test_isProcessRunning(self):
    """test isProcessRunning"""
    self.assertEqual(helper.isProcessRunning("Explorer.exe"), True)
    self.assertEqual(helper.isProcessRunning("nonexistingprocess.exe"), False)

  def test_getVersion(self):
    """test getVersion"""
    self.assertIsNotNone(helper.getVersion("C:\\Windows\\explorer.exe"))
    self.assertEqual(helper.getVersion("C:\\nonexisting.exe"), "")

  def test_moduleCheck(self):
    """test moduleCheck"""
    self.assertEqual(helper.moduleCheck(("os","unittest")), "")
    self.assertNotEqual(helper.moduleCheck(("nonexistingmodule",)), "")

  def test_getWindow(self):
    """test getWindow"""
    self.assertIsNotNone(helper.getWindow(auto.GetRootControl(), "Program Manager"))
    self.assertIsNone(helper.getWindow(auto.GetRootControl(), "NonExistingWindow"))

  def test_controlExists(self):
    """test controlExists"""
    self.assertIsNotNone(helper.controlExists(auto.GetRootControl(), 3, "1"))
    self.assertEqual(helper.controlExists(auto.GetRootControl(), 3, "NonExistingControl"), False)

  def test_waitForControl(self):
    """test waitForControl"""
    self.assertIsNotNone(helper.waitForControl(auto.GetRootControl(), 3, "1"))

if __name__ == '__main__':
  unittest.main()
