"""
The Python Developer Console is a Python interactive console which
automatically reload modules and dependent objects in other module before a new
command is executed.

Known limitations:

- When a dependent module contains 'from foo import bar', and
  reloading foo deletes foo.bar, the dependent module continues to use
  the old foo.bar object rather than failing.
"""

import code
import imp
import logging
import os
import sys
import traceback

class PythonDeveloperConsole(code.InteractiveConsole):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        try:
            import readline
        except ImportError:
            pass
        else:
            import rlcompleter
            
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter('%(name)s - %(levelname)s: %(message)s')
        )

        self.logger = logging.getLogger('PyDevConsole')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)
        
        self.stored_mtimes = {}
        self.check_modules_for_reload()

    def runcode(self, code):
        try:
            self.check_modules_for_reload()
            
            super().runcode(code)
            
            # maybe new modules are loaded
            self.check_modules_for_reload()
        except Exception:
            traceback.print_exc()
    
    def update_objects_for(self, module_name, new_module):
        for other_module_name in sys.modules.keys():
            if other_module_name != module_name:
                other_module_ns = sys.modules[other_module_name].__dict__
        
                for variable in other_module_ns.keys():
                    instance = other_module_ns[variable]
                    instance_class = getattr(instance, '__class__', None)
                    
                    if instance_class != None and (instance_class.__module__ == module_name):
                        self.logger.debug(
                            "update instance '%s' "
                            "in module '%s'" % (variable, other_module_name)
                        )
                        
                        instance.__class__ = getattr(
                            new_module, instance.__class__.__name__
                        )
                        
                        continue
                    
                    instance_module = getattr(instance, '__module__', None)
                    
                    if instance_module == module_name:
                        self.logger.debug(
                            "update class/function '%s' "
                            "in module '%s'" % (variable, other_module_name)
                        )
                        
                        other_module_ns[variable] = getattr(new_module,
                                                            instance.__name__)
            
    
    def check_modules_for_reload(self):
        # because new modules can be loaded during a module reload
        # the size of `sys.modules.items()` can be changed and so we have
        # to make a copy from it via `list()`
        for module_name, module in list(sys.modules.items()):
            # '__main__' module cannot be reloaded
            if module_name != '__main__': 
                module_file = getattr(module, '__file__', None)
                
                if module_file != None and os.path.isfile(module_file):
                    module_mtime = os.path.getmtime(module_file)

                    if module_name in self.stored_mtimes:
                        if module_mtime > self.stored_mtimes[module_name]:
                            self.logger.debug("reload module "
                                              "'%s'" % module_name)
                            
                            new_module = imp.reload(module)
                            
                            self.update_objects_for(module_name, new_module)
                            self.stored_mtimes[module_name] = module_mtime
                    else:
                        self.stored_mtimes[module_name] = module_mtime

if __name__ == '__main__':
    PythonDeveloperConsole().interact("Welcome to the Python Developer "
                                      "Console!")

#__END__
#
# If deleted classes/functions shall not be accessable any more, one can use
# run the following code before module reloading:
#
#   for attr in dir(module):
#       if attr not in ('__name__', '__file__'):
#           delattr(module, attr)