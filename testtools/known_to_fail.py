"""lists all the tests that are known to fail"""
KNOWN_TO_FAIL = [
    "tests/class/getattr2.py",
    "tests/class/oo_diamond.py",
    "tests/class/oo_super.py",
    "tests/namespace/del_global.py",
    "tests/namespace/del_local.py",
    "tests/dict/dictionary3.py",
    "tests/list/listcomp2.py",
    "tests/functions/cmp.py",
    "tests/operator/int-class-priority.py",
    "tests/operator/type-comparison.py",
    "tests/flow/yield.py",

    "tests/libraries/xmlwriter.py",
    "tests/modules/classname.py",
    "tests/modules/from_import.py",
    "tests/modules/import.py",
    "tests/modules/import_alias.py",
    "tests/modules/import_class.py",
    "tests/modules/import_diamond.py",
    "tests/modules/import_global.py",
    "tests/modules/import_multi.py",
    "tests/modules/module_name.py",
    "tests/modules/rng.py",
    
    "tests/import/module_name/module_name.py"# javascript module path is different from
                                             # python module path so equality fails, but
                                             # what the test is actually testing passes
    ]
