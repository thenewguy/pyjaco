#! /usr/bin/python

import optparse
import testtools.runner
import testtools.util
import testtools.tests
import os
from unittest import installHandler
from pyjs import BuiltinGenerator

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
    options, args = option_parser.parse_args()
    
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
    try:
        if options.run_all:
            results = runner.run(testtools.tests.ALL)
        elif options.only_failing:
            results = runner.run(testtools.tests.KNOWN_TO_FAIL)
        elif args:
            results = runner.run(testtools.tests.get_tests(args))
        else:
            results = runner.run(testtools.tests.NOT_KNOWN_TO_FAIL)
    except KeyboardInterrupt:
        pass
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
