$PY.run_module = function (mod_name, run_name) {
	var __name__ = run_name || mod_name;
	var kwargs = {
		"__name__": str(__name__),
		"__builtins__": __builtins__
	};
	return $PY.modules[mod_name](__kwargs_make(kwargs));
}