#! /usr/bin/python

import optparse
import testtools.runner
import testtools.util
import testtools.tests
import os
from unittest import installHandler
from pyjs import BuiltinGenerator
from sys import stdout, stderr
import shutil 

should_remove_suffixes = (
        ".py.js.out",
        ".py.err",
        ".py.js",
        ".py.out",
        ".py.js.err",
        ".py.comp.err",
        ".pyc",
        ".run",
    )
should_remove_files = (
    "tests/test_builtins.js.err",
    "tests/test_builtins.js.out"
)
def should_remove(name):
    name = name.replace("\\", "/")
    if name in should_remove_files:
        return True
    for suffix in should_remove_suffixes:
        if name.endswith(suffix):
            return True
    return False

def write_to_qunit(fp, content, level=0):
    indent = "\t" * level
    if isinstance(content, basestring):
        content = content.splitlines()
    content = ("\n%s" % indent).join(content)
    fp.write(indent + content + "\n")

def main():
    installHandler()
    option_parser = optparse.OptionParser(
        usage="%prog [options] [filenames]",
        description="pyjaco unittests script."
        )
    option_parser.add_option(
        "-a",
        "--run-all",
        action="store_true",
        dest="run_all",
        default=False,
        help="run all tests (including the known-to-fail)"
        )
    option_parser.add_option(
        "-x",
        "--no-error",
        action="store_true",
        dest="no_error",
        default=False,
        help="ignores error (don't display them after tests)"
        )
    option_parser.add_option(
        "-f",
        "--only-failing",
        action="store_true",
        dest="only_failing",
        default=False,
        help="run only failing tests (to check for improvements)"
        )
    option_parser.add_option(
        "-c",
        "--clean-first",
        action="store_true",
        dest="clean_first",
        default=False,
        help="clean tests before running"
        )
    option_parser.add_option(
        "-m",
        "--as-modules",
        action="store_true",
        dest="as_modules",
        default=False,
        help="run tests as modules"
        )
    option_parser.add_option(
        "-s",
        "--as-standard",
        action="store_true",
        dest="as_standard",
        default=False,
        help="run tests as standard"
        )
    option_parser.add_option(
        "-j",
        "--js-exec",
        action="store",
        type="string",
        dest="js_exec",
        default="js",
        help="specify the javascript executable to use"
        )
    option_parser.add_option(
        "-q",
        "--qunit",
        action="store_true",
        dest="qunit",
        default=False,
        help="create qunit tests"
        )
    options, args = option_parser.parse_args()
    
    testtools.util.js_exec = options.js_exec
    
    heading = 'Running tests with "%s"' % testtools.util.js_exec
    print ""
    print "~" * len(heading)
    print heading
    print "~" * len(heading)
    print ""
    
    with open("py-builtins.js", "w") as f:
        builtins = BuiltinGenerator().generate_builtins()
        f.write(builtins)
    
    if options.clean_first:
        for root, dirs, files in os.walk('tests'):
            for name in files:
                path = os.path.join(root, name)
                if should_remove(path):
                    os.remove(path)
                    
    runner = testtools.runner.Py2JsTestRunner(verbosity=2)
    results = None
    test_suites = None
    qunit_title = ""
    try:
        if options.run_all:
            if options.as_modules:
                test_suites = testtools.tests.ALL_MODULES
                qunit_title = "ALL_MODULES"
            elif options.as_standard:
                test_suites = testtools.tests.ALL_STANDARD
                qunit_title = "ALL_STANDARD"
            else:
                test_suites = testtools.tests.ALL
                qunit_title = "ALL"
        elif options.only_failing:
            if options.as_modules:
                test_suites = testtools.tests.MODULE_KNOWN_TO_FAIL
                qunit_title = "MODULE_KNOWN_TO_FAIL"
            elif options.as_standard:
                test_suites = testtools.tests.STANDARD_KNOWN_TO_FAIL
                qunit_title = "STANDARD_KNOWN_TO_FAIL"
            else:
                test_suites = testtools.tests.KNOWN_TO_FAIL
                qunit_title = "KNOWN_TO_FAIL"
        elif args:
            if options.as_modules:
                test_suites = testtools.tests.get_tests(args, test_suite=testtools.tests.ALL_MODULES)
            elif options.as_standard:
                test_suites = testtools.tests.get_tests(args, test_suite=testtools.tests.ALL_STANDARD)
            else:
                test_suites = testtools.tests.get_tests(args)
            qunit_title = "CUSTOM"
        else:
            if options.as_modules:
                test_suites = testtools.tests.MODULE_NOT_KNOWN_TO_FAIL
                qunit_title = "MODULE_NOT_KNOWN_TO_FAIL"
            elif options.as_standard:
                test_suites = testtools.tests.STANDARD_NOT_KNOWN_TO_FAIL
                qunit_title = "STANDARD_NOT_KNOWN_TO_FAIL"
            else:
                test_suites = testtools.tests.NOT_KNOWN_TO_FAIL
                qunit_title = "NOT_KNOWN_TO_FAIL"
        results = runner.run(test_suites)
    except KeyboardInterrupt:
        pass
    if options.qunit:
        heading = 'Creating QUnit Tests'
        print ""
        print "~" * len(heading)
        print heading
        print "~" * len(heading)
        print ""
        output_dir = os.path.join(os.getcwd(), "QUnit/")
        output_test_dir = os.path.join(output_dir, "tests/")
        output_html_path = os.path.join(output_dir, "tests.html")
        for path in (output_test_dir, output_html_path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except:
                pass
        for path in (output_dir, output_test_dir):
            try:
                os.makedirs(path)
            except:
                pass
        qunit_suites = []
        for suite, name in testtools.tests.get_test_names_in_suite(test_suites):
            if hasattr(suite, "templ"):
                qunit_suites.append(suite)
        script_tag = ""
        count = len(qunit_suites)
        i = 1
        for suite in qunit_suites:
            output_test_path = os.path.join(output_test_dir, "%d.js" % i)
            with open(output_test_path, "wb") as fp:
                try:
                    py_out_path = os.path.join(os.getcwd(), suite.templ["py_out_path"])
                except KeyError:
                    stderr.write("Test '%s' cannot be tested with QUnit.\n" % suite)
                    continue
                try:
                    py_js_path = os.path.join(os.getcwd(), suite.templ["js_path"])
                except KeyError:
                    stderr.write("Test '%s' cannot be tested with QUnit.\n" % suite.templ["py_out_path"])
                    continue
                
                if "js_run_file" in suite.templ:
                    py_js_run_file_path = os.path.join(os.getcwd(), suite.templ["js_run_file"])
                else:
                    py_js_run_file_path = ""

                if not os.path.exists(py_out_path) or not os.path.exists(py_js_path) or (py_js_run_file_path and not os.path.exists(py_js_run_file_path)):
                    stderr.write("Could not create QUnit test for '%s'.\n" % suite.templ["js_path"])
                    if not os.path.exists(py_out_path):
                        stderr.write("Python output file '%s' did not exist.\n" % py_out_path)
                    if not os.path.exists(py_js_path):
                        stderr.write("Compiled javascript file '%s' did not exist.\n" % py_js_path)
                    if py_js_run_file_path and not os.path.exists(py_js_run_file_path):
                        stderr.write("Javascript run file '%s' did not exist.\n" % py_js_run_file_path)
                    stderr.write("\n")
                    continue
                
                script_tag += '<script src="%s"></script>' % os.path.relpath(output_test_path, output_dir).replace("\\", "/")

                write_to_qunit(fp, 'test("%s", function() {' % suite.templ["js_path"].replace("\\", "/"))
                write_to_qunit(fp, 'var output = [];', 1)
                write_to_qunit(fp, "var console = {};", 1)
                write_to_qunit(fp, "console.log = function() {", 1)
                write_to_qunit(fp, "var inputs = [];", 2)
                write_to_qunit(fp, "for(var i = 0; i < arguments.length; i++) {", 2)
                write_to_qunit(fp, "inputs[i] = ((arguments[i] != null) && arguments[i]._js_ !== undefined) ? str(arguments[i])._js_() : arguments[i];", 3)
                write_to_qunit(fp, "}", 2)
                write_to_qunit(fp, "output.push(((inputs.length === 0) ? '' : inputs.join(' ')));", 2)
                write_to_qunit(fp, "}", 1)
                write_to_qunit(fp, builtins, 1)
                with open(py_js_path, "rb") as py_js:
                    content = py_js.read().splitlines()
                    if content:
                        del content[0]# remove 'load("py-builtins.js");'
                    write_to_qunit(fp, content, 1)
                if getattr(suite, "imports", None):
                    for imp in suite.imports:
                        with open(imp, "rb") as imp_fp:
                            write_to_qunit(fp, imp_fp.read(), 1)
                if py_js_run_file_path:
                    with open(py_js_run_file_path, "rb") as py_js_run_file:
                        write_to_qunit(fp, py_js_run_file.read(), 1)
                with open(py_out_path, "rb") as py_out:
                    output = py_out.read()
                output = output.replace("\\", "\\\\")
                output = output.replace('"', '\\"')
                output = output.splitlines()
                output = "\\n".join(output)
                write_to_qunit(fp, 'equal(output.join("\\n"), "%s");' % output, 1)
                write_to_qunit(fp, "});")
                stdout.write("QUnit test written: %d%% complete.\r" % (i / count * 100))
                i += 1
        with open(output_html_path, "wb") as fp:
            output = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <title>Pyjaco QUnit Tests -- %s</title>
        <link rel="stylesheet" href="qunit.css">
        <script src="qunit.js"></script>
        %s
    </head>
    <body>
        <div id="qunit"></div>
        <div id="qunit-fixture"></div>
    </body>
</html>
            """ % (qunit_title, script_tag)
            fp.write(output.strip())
        stdout.write("QUnit test written: 100% complete.\n")
    if not options.no_error and results and results.errors:
        print
        print "errors:"
        print "  (use -x to skip this part)"
        for test, error in results.errors:
            print
            print "*", str(test), "*"
            print error

if __name__ == "__main__":
    main()
