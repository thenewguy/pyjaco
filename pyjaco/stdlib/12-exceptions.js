/**
  Copyright 2011 Christian Iversen <ci@sikkerhed.org>

  Permission is hereby granted, free of charge, to any person
  obtaining a copy of this software and associated documentation
  files (the "Software"), to deal in the Software without
  restriction, including without limitation the rights to use,
  copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the
  Software is furnished to do so, subject to the following
  conditions:

  The above copyright notice and this permission notice shall be
  included in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
  OTHER DEALINGS IN THE SOFTWARE.
**/

var BaseException = __inherit(object, "BaseException");

__builtins__.PY$BaseException = BaseException;

BaseException.PY$__init__ = function() {
    if (arguments.length > 0) {
        this.PY$message = arguments[0];
    } else {
        this.PY$message = "";
    }
    this.message = "pyjaco: " + js(this.PY$__class__.PY$__name__) + ": " + js(this.PY$message);
};

BaseException.PY$__str__ = function() {
    return __builtins__.PY$str(this.PY$message);
};

(function() {
     var exceptions = [
         "SystemExit", [],
         "KeyboardInterrupt", [],
         "GeneratorExit", [],
         "Exception", [
             "StopIteration", [],
             "StandardError", [
                 "BufferError", [],
                 "ArithmeticError", [
                     "FloatingPointError", [],
                     "OverflowError", [],
                     "ZeroDivisionError", []
                 ],
                 "AssertionError", [],
                 "AttributeError", [],
                 "EnvironmentError", [
                     "IOError", [],
                     "OSError", []
                 ],
                 "EOFError", [],
                 "ImportError", [],
                 "LookupError", [
                     "IndexError", [],
                     "KeyError", []
                 ],
                 "MemoryError", [],
                 "NameError", [
                     "UnboundLocalError", []
                 ],
                 "ReferenceError", [],
                 "RuntimeError", [
                     "NotImplementedError", []
                 ],
                 "SyntaxError", [
                     "IndentationError", [
                         "TabError", []
                     ]
                 ],
                 "SystemError", [],
                 "TypeError", [],
                 "ValueError", [
                     "UnicodeError", [
                         "UnicodeDecodeError", [],
                         "UnicodeEncodeError", [],
                         "UnicodeTranslateError", []
                     ]
                 ]
             ],
             "Warning", [
                 "DeprecationWarning", [],
                 "PendingDeprecationWarning", [],
                 "RuntimeWarning", [],
                 "SyntaxWarning", [],
                 "UserWarning", [],
                 "FutureWarning", [],
	         "ImportWarning", [],
	         "UnicodeWarning", [],
	         "BytesWarning", []
             ]
         ]
     ];

     function create_exceptions(base, names)
     {
         for (var i = 0; i < names.length; i += 2)
         {
             var name = names[i];
             var subs = names[i+1];
             var exc = __inherit(base, name);
             __builtins__["PY$" + name] = exc;
             create_exceptions(exc, subs);
         }
     }
     create_exceptions(BaseException, exceptions);
})();

$PY.exceptionify = function(err) {
    if (err && err.PY$__class__ !== undefined) {
        return err;
    } else if (err instanceof ReferenceError) {
    	return __builtins__["PY$NameError"](str(err.name + ": " + err.message));
    } else {
    	return err;
    }
}

$PY.c_stopiter = __builtins__.PY$StopIteration("No more items");
