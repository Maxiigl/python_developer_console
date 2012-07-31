from os import path
from python_developer_console import PythonDeveloperConsole
from tempfile import TemporaryDirectory
from unittest import TestCase, TestLoader

import logging
import sys
import time

class PythonDeveloperConsoleTestCase(TestCase):
    
    def setUp(self):
        self.tempdir = TemporaryDirectory()
        self.console = PythonDeveloperConsole()
        self.console.logger.setLevel(logging.WARNING)
        sys.path.append(self.tempdir.name)
    
    def tearDown(self):
        sys.path.remove(self.tempdir.name)
        self.tempdir.cleanup()
        
    def eval(self, expression):
        self.assertFalse(self.console.push("result = %s" % expression))
        
        return self.console.locals["result"]
    
class ModulesWillBeReloadedTestCase(PythonDeveloperConsoleTestCase):
    
    def runTest(self):
        with open(path.join(self.tempdir.name, "foo.py"), 'w') as foo_py:
            foo_py.write(
                "var = 23      \n"
                "              \n"
                "class A:      \n"
                "    var = 23  \n"
                "              \n"
                "def func():   \n"
                "    return 23 \n")
        
        self.console.push("import foo")
        
        self.assertEqual(self.eval("foo.var"), 23)
        self.assertEqual(self.eval("foo.A().var"), 23)
        self.assertEqual(self.eval("foo.func()"), 23)
        
        # we have to wait more than 0.5 seconds (or the module will not be
        # reloaded -> why?! (pythons interal chaching?!)
        time.sleep(1)
        
        with open(path.join(self.tempdir.name, "foo.py"), 'w') as foo_py:
            foo_py.write(
                "var = 42      \n"
                "              \n"
                "class A:      \n"
                "    var = 42  \n"
                "              \n"
                "def func():   \n"
                "    return 42 \n")
        
        self.assertEqual(self.eval("foo.var"), 42)
        self.assertEqual(self.eval("foo.A().var"), 42)
        self.assertEqual(self.eval("foo.func()"), 42)    

class DependentModulesWillBeUpdatedTestCase(PythonDeveloperConsoleTestCase):
    
    def runTest(self):
        with open(path.join(self.tempdir.name, "foo1.py"), 'w') as foo_py:
            foo_py.write(
                "var = 23      \n"
                "              \n"
                "class A:      \n"
                "    var = 23  \n"
                "              \n"
                "def func():   \n"
                "    return 23 \n")
        
        with open(path.join(self.tempdir.name, "foo2.py"), 'w') as foo_py:
            foo_py.write(
                "from foo1 import var, A, func\n"
                "a = A()                      \n"
                "func2 = func                 \n")
            
        self.console.push("import foo2")
        
        self.assertEqual(self.eval("foo2.var"), 23)
        self.assertEqual(self.eval("foo2.A().var"), 23)
        self.assertEqual(self.eval("foo2.func()"), 23)
        self.assertEqual(self.eval("foo2.a.var"), 23)
        self.assertEqual(self.eval("foo2.func2()"), 23)
        
        time.sleep(1)
        
        with open(path.join(self.tempdir.name, "foo1.py"), 'w') as foo_py:
            foo_py.write(
                "var = 42      \n"
                "              \n"
                "class A:      \n"
                "    var = 42  \n"
                "              \n"
                "def func():   \n"
                "    return 42 \n")
        
        # update of var cannot be detected
        self.assertEqual(self.eval("foo2.A().var"), 42)
        self.assertEqual(self.eval("foo2.func()"), 42)
        self.assertEqual(self.eval("foo2.a.var"), 42)
        self.assertEqual(self.eval("foo2.func2()"), 42)