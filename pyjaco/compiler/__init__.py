######################################################################
##
## Copyright 2010-2011 Ondrej Certik <ondrej@certik.cz>
## Copyright 2010-2011 Mateusz Paprocki <mattpap@gmail.com>
## Copyright 2011 Christian Iversen <ci@sikkerhed.org>
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
import inspect
from itertools import chain

class JSError(Exception):
    pass

class BaseCompiler(object):

    name_map = {
        'super' : 'Super',
        'delete': '__delete',
        'default': '__default',
    }

    import __builtin__
    builtin = set([x for x in dir(__builtin__) if not x.startswith("__")])

    def __init__(self, opts, **kwargs):
        self.index_var = 0
        # This is the name of the classes that we are currently in:
        self._class_name = []

        # This lists all variables in the local scope:
        self._vars = []
        self._classes = {}
        self._exceptions = []
        self._funcs = []
        self._global_identifiers = []
        
        self._vars_stack = []
        self._classes_stack = []
        self._exceptions_stack = []
        self._funcs_stack = []
        self._global_identifiers_stack = []
        
        self._scope_level = 0
        
        self.opts = opts
        self.shared_state = kwargs["shared_state"]
        
        self.indention = "    "
    
    @property
    def indent_count(self):
        try:
            i = self.shared_state["indent_count"]
        except KeyError:
            self.shared_state["indent_count"] = i = 0
        return i
    
    @indent_count.setter
    def indent_count(self, value):
        self.shared_state["indent_count"] = value

    def push_scope(self):
        self._vars_stack.append(self._vars)
        self._vars = []
        self._funcs_stack.append(self._funcs)
        self._funcs = []
        self._classes_stack.append(self._classes)
        self._classes = {}
        self._exceptions_stack.append(self._exceptions)
        self._exceptions = []
        self._global_identifiers_stack.append(self._global_identifiers)
        self._global_identifiers = []
        self._scope_level += 1
    
    def pop_scope(self):
        self._vars = self._vars_stack.pop()
        self._funcs = self._funcs_stack.pop()
        self._classes = self._classes_stack.pop()
        self._exceptions = self._exceptions_stack.pop()
        self._global_identifiers = self._global_identifiers_stack.pop()
        self._scope_level -= 1
    
    @property
    def scope_is_global(self):
        return not self._scope_level
    
    @property
    def local_scope(self):
        return chain(self._vars, self._funcs, self._classes, self._exceptions)
    
    @property
    def global_scope(self):
        return chain(*chain(self._vars_stack, self._classes_stack, self._exceptions_stack, self._funcs_stack))
    
    @property
    def scope(self):
        return chain(self.local_scope, self.global_scope)

    @property
    def module(self):
        return self.shared_state.get("module", "")
    
    @property
    def module_ref_prefix(self):
        return "$m__"
    
    @property
    def module_ref(self):
        return "%s%s" % (self.module_ref_prefix, self.module)
    
    def build_ref(self, name):
        if self.module:
            pieces = [self.module_ref]
            if isinstance(name, basestring):
                pieces.append(name)
            else:
                pieces.extend(name)
            return ".PY$".join(pieces)
        else:
            return name

    def alloc_var(self):
        self.index_var += 1
        return "$v%d" % self.index_var

    def visit(self, node):
        try:
            visitor = getattr(self, 'visit_' + self.name(node))
        except AttributeError:
            raise JSError("syntax not supported (%s: %s)" % (node.__class__.__name__, node))

        return visitor(node)

    def increase_indent(self):
        self.indent_count += 1
        
    def decrease_indent(self):
        self.indent_count -= 1

    def indent(self, stmts, indent_count = None):
        if indent_count is None:
            indent_count = self.indent_count
        if isinstance(stmts, basestring):
            stmts = [stmts]
        return [ "%s%s" % (self.indention * indent_count, stmt) for stmt in stmts ]

    ## Shared code

    @staticmethod
    def name(node):
        return node.__class__.__name__

    ## Shared visit functions

    def visit_AssignSimple(self, target, value):
        raise NotImplementedError()

    def visit_Assign(self, node):
        if len(node.targets) > 1:
            tmp = self.alloc_var()
            q = ["var %s = %s" % (tmp, self.visit(node.value))]
            for t in node.targets:
                q.extend(self.visit_AssignSimple(t, tmp))
            return q
        else:
            return self.visit_AssignSimple(node.targets[0], self.visit(node.value))

    def _visit_Exec(self, node):
        pass

    def visit_Print(self, node):
        assert node.dest is None
        assert node.nl
        values = [self.visit(v) for v in node.values]
        values = ", ".join(values)
        return ["__builtins__.PY$print(%s);" % values]

    def visit_Module(self, node):
        module = []

        for stmt in node.body:
            module.extend(self.visit(stmt))

        return module

    def visit_Assert(self, node):
        test = self.visit(node.test)

        if node.msg is not None:
            return ["assert(%s, %s);" % (test, self.visit(node.msg))]
        else:
            return ["assert(%s);" % test]

    def visit_Return(self, node):
        if node.value is not None:
            return ["return %s;" % self.visit(node.value)]
        else:
            return ["return;"]

    def visit_Expr(self, node):
        return [self.visit(node.value) + ";"]

    def visit_Pass(self, node):
        return ["/* pass */"]

    def visit_Break(self, node):
        return ["break;"]

    def visit_Continue(self, node):
        return ["continue;"]

    def visit_arguments(self, node):
        return ", ".join([self.visit(arg) for arg in node.args])
