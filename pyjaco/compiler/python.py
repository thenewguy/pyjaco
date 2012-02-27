######################################################################
##
## Copyright 2011-2012 Christian Iversen <ci@sikkerhed.org>
## Copyright 2010-2011 Ondrej Certik <ondrej@certik.cz>
## Copyright 2010-2011 Mateusz Paprocki <mattpap@gmail.com>
##
## Permission is hereby granted, free of charge, to any person
## obtaining a copy of this software and associated documentation
## files (the "Software"), to deal in the Software without
## restriction, including without limitation the rights to use,
## copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the
## Software is furnished to do so, subject to the following
## conditions:
##
## The above copyright notice and this permission notice shall be
## included in all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
## EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
## OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
## NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
## HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
## WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
## FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
## OTHER DEALINGS IN THE SOFTWARE.
##
######################################################################

import ast
import pyjaco.compiler
from pyjaco.compiler import JSError
from pyjaco.compiler.multiplexer import dump
from utils import special_globals, dotted_to_hierarchy
from itertools import chain

class Compiler(pyjaco.compiler.BaseCompiler):

    obey_getattr_restriction = False

    ops_augassign = {
        "Add"     : "iadd",
        "Sub"     : "isub",
        "Div"     : "idiv",
        "Mult"    : "imul",
        "LShift"  : "ilshift",
        "RShift"  : "irshift",
        "BitOr"   : "ibitor",
        "BitAnd"  : "ibitand",
        "BitXor"  : "ibitxor",
        "FloorDiv": "ifloordiv",
        "Pow"     : "ipow",
    }

    ops_binop = {
        "Add": "add",
        "Sub": "sub",
        "Div": "div",
        "Mod": "mod",
        "Pow": "pow",
        "Mult": "mul",
        "BitOr": "bitor",
        "BitAnd": "bitand",
        "BitXor": "bitxor",
        "LShift": "lshift",
        "RShift": "rshift",
        "FloorDiv": "floordiv",
    }

    ops_compare = {
        "Eq": "eq",
        "NotEq": "ne",
        "Gt": "gt",
        "Lt": "lt",
        "GtE": "ge",
        "LtE": "le",
    }

    def __init__(self, opts, **kwargs):
        super(Compiler, self).__init__(opts, **kwargs)
        self.future_division = False
        self.opts = opts

    def stack_destiny(self, names, skip):
        for name in reversed(self.stack[:-skip]):
            if name in names:
                return name
        else:
            return False

    def visit_Name(self, node):
        name = self.name_map.get(node.id, node.id)
        
        if name in special_globals.keys():
            pass
        elif name in self.local_scope:
            pass
        elif self.build_ref(name) in self.local_scope:
            name = self.build_ref(name)
        elif name in self.global_scope:
            pass
        elif self.build_ref(name) in self.global_scope:
            name = self.build_ref(name)
        elif name in self.builtin:
            name = "__builtins__.PY$" + name
            
        return name

    def visit_Return(self, node):
        if node.value is not None:
            return ["return %s;" % self.visit(node.value)]
        else:
            return ["return None;"]

    def visit_Global(self, node):
        self._vars.extend(node.names)
        return []

    def visit_FunctionDef(self, node):
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults

        if node.args.kwarg:
            kwarg_name = node.args.kwarg
        else:
            kwarg_name = "__kwargs"

        if node.args.vararg:
            vararg_name = node.args.vararg
        else:
            vararg_name = "__varargs"

        if len(node.args.args) and node.args.args[0].id == "self":
            offset = 1
        else:
            offset = 0

        inclass = self.stack_destiny(["ClassDef", "FunctionDef"], 2) in ["ClassDef"]

        if inclass:
            js = ["function() {"]
        elif self.module:
            js = ["%s = function() {" % self.build_ref(node.name)]
            self._funcs.append(self.build_ref(node.name))
        else:
            js = ["var %s = function() {" % (node.name)]
            self._funcs.append(node.name)

        self.push_scope()

        self._vars = [arg.id for arg in node.args.args]
        
        self.increase_indent()

        if inclass or offset == 1:
            js.extend(self.indent(["var self = this;"]))

        newargs = self.alloc_var()

        js.extend(self.indent(["var %s = __kwargs_get(arguments);" % kwarg_name]))
        js.extend(self.indent(["var %s = __varargs_get(arguments);" % vararg_name]))
        js.extend(self.indent(["var %s = Array.prototype.slice.call(arguments).concat(js(%s));" % (newargs, vararg_name)]))
        for i, arg in enumerate(node.args.args[offset:]):
            if not isinstance(arg, ast.Name):
                raise JSError("tuples in argument list are not supported")

            values = dict(i = i, id = self.visit(arg), rawid = arg.id, kwarg = kwarg_name, newargs = newargs, func = node.name, indent = self.indention)
            if len(self._class_name):
                values['fullfunc'] = "%s.%s" % (self._class_name[-1], node.name)
            else:
                values['fullfunc'] = node.name

            if defaults[i + offset] == None:
                js.extend(self.indent(["var %(id)s = ('%(rawid)s' in %(kwarg)s) ? %(kwarg)s['%(rawid)s'] : %(newargs)s[%(i)d];" % values]))
            else:
                values['default'] = self.visit(defaults[i + offset])
                js.extend(self.indent(["var %(id)s = %(newargs)s[%(i)d];" % values]))
                js.extend(self.indent(["if (%(id)s === undefined) { %(id)s = %(kwarg)s.%(rawid)s === undefined ? %(default)s : %(kwarg)s.%(rawid)s; };" % values]))
            js.extend(self.indent(["delete %(kwarg)s.%(id)s" % values]))
            if self.opts['check_params']:
                js.extend(self.indent([
                    "if (%(id)s === undefined) {" % values,
                    "%(indent)s__builtins__.PY$print('%(fullfunc)s() did not get parameter %(id)s');"  % values,
                    "};"
                ]))

        if node.name in ["__getattr__", "__setattr__"]:
            js.extend(self.indent(["if (typeof %(id)s === 'string') { %(id)s = str(%(id)s); };" % { 'id': node.args.args[1].id }]))

        if node.args.kwarg:
            js.extend(self.indent(["%s = dict(%s);" % (node.args.kwarg, node.args.kwarg)]))

        if node.args.vararg:
            l = len(node.args.args)
            if inclass:
                l -= 1
            js.extend(self.indent(["%s = tuple(%s.slice(%s));" % (node.args.vararg, newargs, l)]))

        for stmt in node.body:
            js.extend(self.indent(self.visit(stmt)))

        self.pop_scope()
        if not (node.body and isinstance(node.body[-1], ast.Return)):
            js.extend(self.indent("return None;"))
        
        self.decrease_indent()
        js.extend(self.indent("}"))

        for dec in node.decorator_list:
            js.extend(["%s.PY$%s = %s(%s.PY$__getattr__('%s'));" % (self.heirar, node.name, self.visit(dec), self.heirar, node.name)])

        return js

    def visit_ClassDef(self, node):
        js = []
        bases = [self.visit(n) for n in node.bases]
        if not bases:
            bases = ['object']
        if len(bases) == 0:
            raise JSError("Old-style classes not supported")
        elif len(bases) > 1:
            raise JSError("Multiple inheritance not supported")

        class_name = node.name
        class_ref = self.build_ref(class_name)
        #self._classes remembers all classes defined
        self._classes[class_ref] = node

        use_prototypes = "false" if any([isinstance(x, ast.FunctionDef) and x.name == "__call__" for x in node.body]) else "true"
        if len(self._class_name) > 0:
            js.append("__inherit(%s, '%s', %s);" % (bases[0], class_name, use_prototypes))
        else:
            js.append("%s%s = __inherit(%s, '%s', %s);" % (
                    "" if self.module else "var ",
                    class_ref,
                    bases[0],
                    class_name,
                    use_prototypes
                )
            )

        self.push_scope()
        self._class_name.append(class_name)
        heirar = self.build_ref(".PY$".join(self._class_name + []))
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                value = self.visit(stmt.value)
                for t in stmt.targets:
                    js.append("%s.PY$%s = %s;" % (heirar, t.id, value))
            elif isinstance(stmt, ast.FunctionDef):
                self.heirar = heirar
                js.append("%s.PY$%s = %s;" % (heirar, stmt.name, "\n".join(self.visit(stmt))))
            elif isinstance(stmt, ast.ClassDef):
                js.append("%s.PY$%s = %s;" % (heirar, stmt.name, "\n".join(self.visit(stmt))))
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
                js.append("\n".join(["/* %s */" % s for s in stmt.value.s.split("\n")]))
            elif isinstance(stmt, ast.Pass):
                # Not required for js
                pass
            else:
                raise JSError("Unsupported class data: %s" % stmt)
        self._class_name.pop()
        self.pop_scope()

        return js

    def visit_Delete(self, node):
        return [self.visit_DeleteSimple(part) for part in node.targets]

    def visit_DeleteSimple(self, node):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Index):
            js = "%s.PY$__delitem__(%s);" % (self.visit(node.value), self.visit(node.slice))
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            js = "%s.PY$__delslice__(%s, %s);" % (self.visit(node.value), self.visit(node.slice.lower), self.visit(node.slice.upper))
        elif isinstance(node, ast.Attribute):
            js = "%s.PY$__delattr__('%s');" % (self.visit(node.value), node.attr)
        elif isinstance(node, ast.Name):
            raise JSError("Javascript does not support deleting variables. Cannot compile")
        else:
            raise JSError("Unsupported delete type: %s" % node)

        return js

    def visit_AssignSimple(self, target, value):
        if isinstance(target, (ast.Tuple, ast.List)):
            dummy = self.alloc_var()
            js = ["var %s = %s;" % (dummy, value)]

            for i, target in enumerate(target.elts):
                var = self.visit(target)
                declare = ""
                if isinstance(target, ast.Name):
                    if not (var in self._vars):
                        self._vars.append(var)
                        declare = "var "
                js.append("%s%s = %s.PY$__getitem__(%d);" % (declare, var, dummy, i))
        elif isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Index):
            # found index assignment
            js = ["%s.PY$__setitem__(%s, %s);" % (self.visit(target.value), self.visit(target.slice), value)]
        elif isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Slice):
            # found slice assignmnet
            js = ["%s.PY$__setslice__(%s, %s, %s);" % (self.visit(target.value), self.visit(target.slice.lower), self.visit(target.slice.upper), value)]
        else:
            if isinstance(target, ast.Name):
                var = target.id
                if self.scope_is_global:
                    var = self.build_ref(var)
                declare = ""
                if not var in self.local_scope:
                    self._vars.append(var)
                    if not self.module or not var.startswith(self.module_ref):
                        declare = "var "
                js = ["%s%s = %s;" % (declare, var, value)]
            elif isinstance(target, ast.Attribute):
                js = ["%s.PY$__setattr__('%s', %s);" % (self.visit(target.value), str(target.attr), value)]
            else:
                raise JSError("Unsupported assignment type")
        return js

    def visit_AugAssign(self, node):
        target = self.visit(node.target)
        value = self.visit(node.value)

        if not self.future_division and isinstance(node.op, ast.Div):
            node.op = ast.FloorDiv()

        name = node.op.__class__.__name__
        if name in self.ops_augassign:
            return self.visit_AssignSimple(node.target,
                "%s.PY$__%s__(%s)" % (target, self.ops_augassign[name], value))
        else:
            raise JSError("Unsupported AugAssign type %s" % node.op)

    def visit_For(self, node):
        if isinstance(node.target, ast.Name):
            for_target = self.visit(node.target)
        elif isinstance(node.target, ast.Tuple):
            for_target = self.alloc_var()
        else:
            raise JSError("Advanced for-loop decomposition not supported")

        js = []

        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range" and not node.orelse:
            counter  = self.visit(node.target)
            end_var  = self.alloc_var()
            assert(len(node.iter.args) in (1,2,3))
            if len(node.iter.args) == 1:
                start = "$c0"
                end   = self.visit(node.iter.args[0])
                step  = "$c1"
            elif len(node.iter.args) == 2:
                start = self.visit(node.iter.args[0])
                end   = self.visit(node.iter.args[1])
                step  = "$c1"
            else:
                start = self.visit(node.iter.args[0])
                end   = self.visit(node.iter.args[1])
                step  = self.visit(node.iter.args[2])

            js.append("%s = %s;" % (end_var, end))
            if step <> "$c1":
                step_var = self.alloc_var()
                js.append("%s = %s;" % (step_var, step));
            else:
                step_var = step
            js.append("for (%s = %s; %s.PY$__lt__(%s) == True; %s = %s.PY$__add__(%s)) {" % (counter, start, counter, end_var, counter, counter, step_var))
            for stmt in node.body:
                js.extend(self.indent(self.visit(stmt)))
            js.append("}")
            return js


        for_iter = self.visit(node.iter)

        iter_var = self.alloc_var()
        exc_var = self.alloc_var()

        if node.orelse:
            orelse_var = self.alloc_var()
            js.append("var %s = true;" % orelse_var)

        js.append("var %s;" % for_target);
        for_init = "var %s = iter(%s)" % (iter_var, for_iter)
        for_iter = "%s = $PY.next(%s)" % (for_target, iter_var)
        for_cond = "%s !== null" % (for_target)
        js.append("  for (%s; %s; %s) {" % (for_init, for_iter, for_cond))
        if isinstance(node.target, ast.Tuple):
            js.append("    %s;" % "; ".join(["var %s = %s.PY$__getitem__(%s)" % (x.id, for_target, i) for i, x in enumerate(node.target.elts)]))

        for stmt in node.body:
            js.extend(self.indent(self.visit(stmt)))

        js.append("  }")

        if node.orelse:
            js.append("if (%s) {" % orelse_var)
            for stmt in node.orelse:
                js.extend(self.indent(self.visit(stmt)))
            js.append("  }")

        return js

    def visit_While(self, node):
        js = []

        if node.orelse:
            orelse_var = self.alloc_var()
            js.append("var %s = true;" % orelse_var)

        js.append("while (bool(%s) === True) {" % self.visit(node.test))
        if node.orelse:
            js.extend(self.indent(["var %s = true;" % orelse_var]))

        for stmt in node.body:
            js.extend(self.indent(self.visit(stmt)))

        js.append("}")

        if node.orelse:
            js.append("if (%s) {" % orelse_var)

            for stmt in node.orelse:
                js.extend(self.indent(self.visit(stmt)))

            js.append("}")

        return js

    def visit_If(self, node):
        js = ["if (bool(%s) === True) {" % self.visit(node.test)]

        for stmt in node.body:
            js.extend(self.indent(self.visit(stmt)))

        if node.orelse:
            js.append("} else {")

            for stmt in node.orelse:
                js.extend(self.indent(self.visit(stmt)))

        return js + ["}"]

    def _visit_With(self, node):
        pass

    def visit_TryExcept(self, node):
        if node.orelse:
            raise JSError("Try-Except with else-clause not supported")

        js = []
        js.append("try {")
        for n in node.body:
            js.extend(self.indent(self.visit(n)))
        err = self.alloc_var()
        self._exceptions.append(err)
        js.append("} catch (%s) {" % err)
        catchall = False
        for i, n in enumerate(node.handlers):
            if i > 0:
                pre = "else "
            else:
                pre = ""
            if n.type:
                if isinstance(n.type, ast.Name):
                    js.extend(self.indent(["%sif ($PY.isinstance(%s, %s)) {" % (pre, err, self.visit(n.type))]))
                else:
                    raise JSError("Catching non-simple exceptions not supported")
            else:
                catchall = True
                js.append("%sif (true) {" % (pre))

            if n.name:
                if isinstance(n.name, ast.Name):
                    js.append(self.indent(["var %s = %s;" % (self.visit(n.name), err)])[0])
                else:
                    raise JSError("Catching non-simple exceptions not supported")

            for b in n.body:
                js.extend(self.indent(self.visit(b)))

            js.append("}")

        if not catchall:
            js.append("else { throw %s; }" % err);

        js.append("};")
        self._exceptions.pop()
        return js

    def visit_TryFinally(self, node):
        js = []
        exc_var = self.alloc_var()
        exc_store = self.alloc_var()
        js.append("var %s;" % exc_store)
        js.append("try {")
        for n in node.body:
            js.append("\n".join(self.visit(n)))
        js.append("} catch (%s) { %s = %s; }" % (exc_var, exc_store, exc_var))
        for n in node.finalbody:
            js.append("\n".join(self.visit(n)))
        js.append("if (%s) { throw %s; }" % (exc_store, exc_store))
        return js

    def visit_Import(self, node):
        stmts = []
        for node in node.names:
            var = node.asname if node.asname else node.name
            hierarchy = dotted_to_hierarchy(var)
            var = var.replace('.', '.PY$')
            declare = ""
            if len(hierarchy) > 1:
                for i, x in enumerate(hierarchy):
                    y = x.replace('.', '.PY$') 
                    ts = []
                    if not i and not x in self.local_scope:
                        stmt = "var %(x)s;"
                        ts.append(stmt)
                        self._vars.append(x)
                    stmt = "%(y)s = %(y)s || module('%(x)s', '<empty placeholder>', {});"
                    ts.append(stmt)
                    stmts.extend([t % {"x": x, "y": y} for t in ts])
                del stmts[-1]
            elif not var in self.local_scope:
                declare = "var "
                self._vars.append(var)
            stmt = "%s%s = __import__('%s', js(__module__));" % (declare, var, node.name)
            stmts.append(stmt)
        return stmts

    def visit_ImportFrom(self, node):
        stmts = []
        if node.module == "__future__":
            if len(node.names) == 1 and node.names[0].name == "division":
                self.future_division = True
            else:
                raise JSError("Unknown import from __future__: %s" % node.names[0].name)
        elif node.module == "__javascript__":
            raise JSError("import from __javascript__ is not supported yet")
        else:
            module = node.module
            catch_var = self.alloc_var()
            stmts.append("var %s;" % catch_var)
            for node in node.names:
                var = node.asname if node.asname else node.name
                if not var in self.local_scope:
                    declare = "var "
                    self._vars.append(var)
                else:
                    declare = ""
                stmt = []
                stmt.append("%s%s%s = __import__('%s', js(__module__)).PY$__getattr__('%s');" % (
                        self.indention,
                        declare,
                        var,
                        module,
                        node.name
                    )
                )
                stmt.append("} catch (%s) {" % catch_var)
                stmt.append("%sif ($PY.isinstance(%s, __builtins__.PY$AttributeError)) {" % (self.indention, catch_var))
                stmt.append("%s%sthrow __builtins__.PY$ImportError('Could not find %s');" % (
                        self.indention,
                        self.indention,
                        node.name
                    )
                )
                stmt.append("%s} else {" % self.indention)
                stmt.append("%s%sthrow %s;" % (self.indention, self.indention, catch_var))
                stmt.append("%s}" % self.indention)
                stmt.append("}")
                stmts.append("\n".join(chain(["try {"], self.indent(stmt))))
        return stmts

    def visit_Lambda(self, node):
        node_args = self.visit(node.args)
        node_body = self.visit(node.body)
        return "function(%s) {return %s;}" % (node_args, node_body)

    def visit_BoolOp(self, node):
        assign = self.stack_destiny(["Assign", "FunctionDef", "Print", "Call", "comprehension"], 1) in ["Assign", "Print", "Call"]

        if isinstance(node.op, ast.And):
            op = " && "
        elif isinstance(node.op, ast.Or):
            op = " || "
        else:
            raise JSError("Unknown boolean operation %s" % node.op)

        if assign:
            var = self.alloc_var()
            return "function() { var %s; %s; return %s; }()" % (var, op.join(["bool(%s = %s) === True" % (var, self.visit(val)) for val in node.values]), var)
        else:
            return op.join(["bool(%s) === True" % self.visit(val) for val in node.values])

    def visit_UnaryOp(self, node):
        if   isinstance(node.op, ast.USub  ): return "%s.PY$__neg__()"            % (self.visit(node.operand))
        elif isinstance(node.op, ast.UAdd  ): return "%s.PY$__pos__()"            % (self.visit(node.operand))
        elif isinstance(node.op, ast.Invert): return "%s.PY$__invert__()"         % (self.visit(node.operand))
        elif isinstance(node.op, ast.Not   ): return "$PY.__not__(%s)" % (self.visit(node.operand))
        else:
            raise JSError("Unsupported unary op %s" % node.op)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Str):
            return "%s.PY$__mod__(%s)" % (left, right)

        if not self.future_division and isinstance(node.op, ast.Div):
            node.op = ast.FloorDiv()

        name = node.op.__class__.__name__

        if name in self.ops_binop:
            return "%s.PY$__%s__(%s)" % (left, self.ops_binop[name], right)
        else:
            raise JSError("Unknown binary operation type %s" % node.op)

    def visit_Compare(self, node):
        assert len(node.ops) == 1
        assert len(node.comparators) == 1
        op = node.ops[0]
        comp = node.comparators[0]

        name = op.__class__.__name__

        if name in self.ops_compare:
            return "%s.PY$__%s__(%s)" % (self.visit(node.left), self.ops_compare[name], self.visit(comp))
        elif isinstance(op, ast.In):
            return "%s.PY$__contains__(%s)" % (self.visit(comp), self.visit(node.left))
        elif isinstance(op, ast.Is):
            return "$PY.__is__(%s, %s)" % (self.visit(node.left), self.visit(comp))
        elif isinstance(op, ast.NotIn):
            return "$PY.__not__(%s.PY$__contains__(%s))" % (self.visit(comp), self.visit(node.left))
        else:
            raise JSError("Unknown comparison type %s" % node.ops[0])

    def visit_Num(self, node):
        if isinstance(node.n, (int, long)):
            if (0 <= node.n <= 9):
                return "$c%s" % str(node.n)
            elif -2**30 < node.n < 2**30:
                return "int(%s)" % str(node.n)
            else:
                raise JSError("Long integer type outside of javascript range")
        elif isinstance(node.n, float):
            return "float(%s)" % node.n
        else:
            raise JSError("Unknown numeric type: %s" % node.n.__class__.__name__)

    def visit_Str(self, node):
        # Uses the Python builtin repr() of a string and the strip string type
        # from it. This is to ensure Javascriptness, even when they use things
        # like b"\\x00" or u"\\u0000".
        return "str(%s)" % repr(node.s).lstrip("urb")

    def visit_Call(self, node):
        js = []
        func = self.visit(node.func)
        compound = ("Assign" in self.stack) or ("AugAssign" in self.stack) or (self.stack.count("Call") > 1)

        if node.keywords or node.kwargs:
            keywords = []
            for kw in node.keywords:
                keywords.append("%s: %s" % (kw.arg, self.visit(kw.value)))
            if node.kwargs:
                kwparam = ", %s" % self.visit(node.kwargs)
            else:
                kwparam = ""
            kwargs = ["__kwargs_make({%s}%s)" % (", ".join(keywords), kwparam)]
        else:
            kwargs = []

        if node.starargs:
            varargs = ["__varargs_make(%s)" % self.visit(node.starargs)]
        else:
            varargs = []

        js_args = ", ".join([ self.visit(arg) for arg in node.args ] + varargs + kwargs)

        js.append("%s(%s)" % (func, js_args))

        return "\n".join(js)

    def visit_Raise(self, node):
        assert node.inst is None
        assert node.tback is None
        if not node.type:
            return ["throw %s;" % self._exceptions[-1]]
        else:
            if isinstance(node.type, ast.Name) and node.type.id in self.builtin:
                return ["throw %s();" % self.visit(node.type)]
            elif isinstance(node.type, (ast.Call, ast.Name)):
                return ["throw %s;" % self.visit(node.type)]
            else:
                raise JSError("Unknown exception type")

    def visit_Attribute(self, node):
        if node.attr.startswith("__") and self.obey_getattr_restriction:
            return """%s.PY$%s""" % (self.visit(node.value), node.attr)
        else:
            return """%s.PY$__getattr__('%s')""" % (self.visit(node.value), node.attr)

    def visit_Tuple(self, node):
        els = [self.visit(e) for e in node.elts]
        return "tuple([%s])" % (", ".join(els))

    def visit_Dict(self, node):
        els = []
        for k, v in zip(node.keys, node.values):
            els.append("%s, %s" % (self.visit(k), self.visit(v)))
        return "dict([%s])" % (", ".join(els))

    def visit_List(self, node):
        els = [self.visit(e) for e in node.elts]
        return "list([%s])" % (", ".join(els))

    def visit_comprehension(self, node):
        if isinstance(node.target, ast.Name):
            var = self.visit(node.target)
        elif isinstance(node.target, ast.Tuple):
            var = self.alloc_var()
        else:
            raise JSError("Unsupported target type in list comprehension")
        iter_var = self.alloc_var()
        res = "var %s; for (var %s = iter(%s); %s = $PY.next(%s); %s !== null) {\n" % (var, iter_var, self.visit(node.iter), var, iter_var, var)
        if isinstance(node.target, ast.Tuple):
            for i, el in enumerate(node.target.elts):
                if isinstance(el, ast.Name):
                    n = self.visit(el)
                else:
                    raise JSError("Invalid tuple element in list comprehension")
                res += "var %s = %s.PY$__getitem__($c%d);\n" % (n, var, i)

        if node.ifs:
            ifexp = []
            for exp in node.ifs:
                ifexp.append("bool(%s) === False" % self.visit(exp))
            res += "if (%s) { continue; }" % (" || ".join(ifexp))
        return res

    def visit_ListComp(self, node):
        res_var = self.alloc_var()
        exp = "%s.PY$append(%s)" % (res_var, self.visit(node.elt))
        for x in node.generators:
            exp = "%s %s}" % (self.visit(x), exp)

        return "(function() {var %s = list(); %s; return %s})()" % (res_var, exp, res_var)

    def visit_GeneratorExp(self, node):
        if not len(node.generators) == 1:
            raise JSError("Compound generator expressions not supported")
        if not isinstance(node.generators[0].target, ast.Name):
            raise JSError("Non-simple targets in generator expressions not supported")

        return "__builtins__.PY$map(function(%s) {return %s;}, %s)" % (node.generators[0].target.id, self.visit(node.elt), self.visit(node.generators[0].iter))

    def visit_Slice(self, node):
        if node.lower and node.upper and node.step:
            return "slice(%s, %s, %s)" % (self.visit(node.lower),
                    self.visit(node.upper), self.visit(node.step))
        if node.lower and node.upper:
            return "slice(%s, %s)" % (self.visit(node.lower),
                    self.visit(node.upper))
        if node.upper and not node.step:
            return "slice(%s)" % (self.visit(node.upper))
        if node.lower and not node.step:
            return "slice(%s, null)" % (self.visit(node.lower))
        if not node.lower and not node.upper and not node.step:
            return "slice(null)"
        raise NotImplementedError("Slice")

    def visit_Subscript(self, node):
        return "%s.PY$__getitem__(%s)" % (self.visit(node.value), self.visit(node.slice))

    def visit_Index(self, node):
        return self.visit(node.value)
