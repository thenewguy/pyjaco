$PY.__import_cache = {};

function __import__(name, dotted_caller) {
	
	if(!(name in $PY.modules)) {
		var dotted_array = dotted_caller.split('.');
		dotted_array = dotted_array.slice(0,-1);
		var tempname = dotted_array.join('.') + '.' + name;
		if(!(tempname in $PY.modules)) {
			tempname = dotted_caller + '.' + name;
			if(!(tempname in $PY.modules)) {
				throw __builtins__.PY$ImportError(str('Could not import "'+name+'".'));
			}
		}
		name = tempname;
	}
	
	var module = $PY.__import_cache[name];
	
	if(module === undefined) {
		var kwargs = {
			"__name__": name,
			"__builtins__": __builtins__,
			"__module__": str(name)
		};
		module = $PY.__import_cache[name] = $PY.modules[name](__kwargs_make(kwargs));
	}
	
	return module;
}