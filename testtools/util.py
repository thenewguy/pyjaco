"""
Module that defines Tool functions and test runners/result for use with
the unittest library.
"""
import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
import os
import subprocess
import posixpath
from os.path import split, splitext

def run_command(cmd):
    return subprocess.call(cmd, shell = True)

def get_posix_path(path):
    """translates path to a posix path"""
    heads = []
    tail = path
    while tail != '':
        tail, head = os.path.split(tail)
        heads.append(head)
    return posixpath.join(*heads[::-1])

def run_with_stdlib(file_path, file_name=None):
    """Creates a test that runs a js file with the stdlib."""
    file_name = file_name if file_name else file_path

    class TestStdLib(unittest.TestCase):
        """Tests js code with the stdlib"""
        templ = {
            "js_path": file_path, 
            "js_unix_path": get_posix_path(file_path), 
            "js_out_path": file_path + ".out",
            "js_error": file_path + ".err",
            "name": file_name,
        }
        def reportProgres(self):
            """Should be overloaded by the test result class."""
    
        def runTest(self):
            """The actual test goes here."""
            cmd = (
                  'js -f "py-builtins.js" '
                  '-f "%(js_path)s" > "%(js_out_path)s" 2> "%(js_error)s"'
                  )% self.templ
            self.assertEqual(0, run_command(cmd))
            self.reportProgres()
        def __str__(self):
            return "%(js_unix_path)s [1]: " % self.templ

    return TestStdLib

def compile_file_test(file_path, file_name=None):
    """Creates a test that tests if a file can be compiled by python"""
    file_name = file_name if file_name else file_path
    
    class CompileFile(unittest.TestCase):
        """Test if a file can be compiled by python."""

        templ = {
            "py_executable": sys.executable,
            "py_path": file_path, 
            "py_unix_path": get_posix_path(file_path), 
            "py_out_path": file_path + ".out",
            "py_error": file_path + ".err",
            "name": file_name,
        }
        def reportProgres(self):
            """Should be overloaded by the test result class"""

        def runTest(self):
            """The actual test goes here."""
            commands = (
                (
                '%(py_executable)s "%(py_path)s" > '
                '"%(py_out_path)s" 2> "%(py_error)s"'
                ) % self.templ,
              )
            for cmd in commands:
                self.assertEqual(0, run_command(cmd))
                self.reportProgres()
        def __str__(self):
            return "%(py_unix_path)s [1]: " % self.templ
    return CompileFile




def compile_and_run_file_test(file_path, file_name=None):
    """Creates a test that compiles and runs the python file as js"""
    file_name = file_name if file_name else file_path

    class CompileAndRunFile(unittest.TestCase):
        """Tests that a file can be compiled and run as js"""
        templ = {
        "py_executable": sys.executable,
        "py_path": file_path, 
        "py_unix_path": get_posix_path(file_path),
        "py_out_path": file_path + ".out",
        "js_path": file_path + ".js",
        "js_out_path": file_path + ".js.out",
        "py_error": file_path + ".err",
        "js_error": file_path + ".js.err",
        "compiler_error": file_path + ".comp.err",
        "name": file_name,
        }
        def reportProgres(self):
            """Should be overloaded by the test result class"""

        def runTest(self):
            """The actual test goes here."""
            mtime_src = os.path.getmtime(self.templ['py_path'])
            try:
                mtime_py_res = os.path.getmtime(self.templ['py_out_path'])
            except OSError:
                mtime_py_res = 0
            python_command = (
                '%(py_executable)s "%(py_path)s" > "%(py_out_path)s" 2> '
                '"%(py_error)s"'
                ) % self.templ

            try:
                mtime_js_res = os.path.getmtime(self.templ['js_path'])
            except OSError:
                mtime_js_res = 0
            compile_command = (
                '%(py_executable)s pyjs.py -I -q '
                '"%(py_path)s" > "%(js_path)s" 2> '
                '"%(compiler_error)s"'
                ) % self.templ 

            javascript_command = (
                'js -f "%(js_path)s" > "%(js_out_path)s" 2> '
                '"%(js_error)s"' 
                ) % self.templ

            commands = []
            if mtime_py_res < mtime_src:
                commands.append(python_command)
            if mtime_js_res < mtime_src:
                commands.append(compile_command)
            commands.append(javascript_command)

            for cmd in commands:
                self.assertEqual(0, run_command(cmd))
                self.reportProgres()
            self.assertEqual(
                file(self.templ["py_out_path"]).readlines(),
                file(self.templ["js_out_path"]).readlines()
                )
            self.reportProgres()

        def __str__(self):
            return "%(py_unix_path)s: " % self.templ

    return CompileAndRunFile

def compile_and_run_file_failing_test(*a, **k):
    """Turn a test to a failing test"""
    _class = compile_and_run_file_test(*a, **k)

    class FailingTest(_class):
        """Failing test"""
        @unittest.expectedFailure
        def runTest(self):
            return super(FailingTest, self).runTest()

    return FailingTest

def compile_as_module_and_run_file_test(file_path, file_name=None, output_postfix=None, uses_imports = False):
    """Creates a test that compiles as a module and runs the python file as js"""
    file_name = file_name if file_name else file_path

    class CompileAsModuleAndRunFile(unittest.TestCase):
        """Tests that a file can be compiled and run as js"""
        if output_postfix:
            (head, tail) = split(file_path.replace("\\", "/"))
            (root, ext) = splitext(tail)
            output_path = "%s/%s_%s%s" % (head.rstrip("/"), root, output_postfix, ext)
        else:
            output_path = file_path
        templ = {
            "py_executable": sys.executable,
            "py_path": file_path, 
            "py_unix_path": get_posix_path(file_path),
            "write_test_as": get_posix_path(output_path),
            "py_out_path": output_path + ".out",
            "js_path": output_path + ".js",
            "js_run_file": output_path + ".js.run",
            "js_out_path": output_path + ".js.out",
            "py_error": output_path + ".err",
            "js_error": output_path + ".js.err",
            "compiler_error": output_path + ".comp.err",
            "name": file_name,
        }
        def reportProgres(self):
            """Should be overloaded by the test result class"""

        def runTest(self):
            """The actual test goes here."""
            mtime_src = os.path.getmtime(self.templ['py_path'])
            try:
                mtime_py_res = os.path.getmtime(self.templ['py_out_path'])
            except OSError:
                mtime_py_res = 0
            python_command = (
                '%(py_executable)s "%(py_path)s" > "%(py_out_path)s" 2> '
                '"%(py_error)s"'
                ) % self.templ

            try:
                mtime_js_res = os.path.getmtime(self.templ['js_path'])
            except OSError:
                mtime_js_res = 0
            compile_command = (
                '%(py_executable)s pyjs.py -I -q -m '
                '"%(py_path)s" > "%(js_path)s" 2> '
                '"%(compiler_error)s"'
                ) % self.templ 
            
            templ = self.templ.copy()
            import_commands = []
            templ["import_js"] = ""
            
            if uses_imports:
                dirpath = os.path.dirname(file_path)
                for root, dirs, files in os.walk(dirpath):
                    for fn in [x for x in files if x.endswith('.py')]:
                        py_path = os.path.join(root, fn).replace("\\","/")
                        if py_path == self.templ["py_path"].replace("\\","/"):
                            continue
                        js_path = py_path + ".js"
                        cmd = (
                            '%(py_executable)s pyjs.py -q -m '
                            '"%(py_path)s" > "%(js_path)s"'
                        ) % {
                             "py_executable": self.templ["py_executable"],
                             "py_path": py_path,
                             "js_path": js_path
                        }
                        import_commands.append(cmd)
                        templ["import_js"] = '%s -f "%s"' % (templ["import_js"], js_path)
                        
            
            javascript_command = (
                'js -f "%(js_path)s" %(import_js)s -f "%(js_run_file)s" > "%(js_out_path)s" 2> '
                '"%(js_error)s"' 
                ) % templ
                
            # create javascript run file
            with open(self.templ['js_run_file'], 'w') as f:
                dotted = os.path.splitext(self.templ['py_path'])[0].replace("\\","/").replace("/",".")
                f.write("\n")
                f.write("$PY.run_module('%s', '__main__')" % dotted)

            commands = []
            if mtime_py_res < mtime_src:
                commands.append(python_command)
            if mtime_js_res < mtime_src:
                commands.append(compile_command)
            commands.extend(import_commands)
            commands.append(javascript_command)

            for cmd in commands:
                self.assertEqual(0, run_command(cmd))
                self.reportProgres()
            self.assertEqual(
                file(self.templ["py_out_path"]).readlines(),
                file(self.templ["js_out_path"]).readlines()
                )
            self.reportProgres()

        def __str__(self):
            return "%(py_unix_path)s: " % self.templ
        
        def write_test_as(self):
            return "%(write_test_as)s: " % self.templ

    return CompileAsModuleAndRunFile