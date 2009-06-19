import logging
from flexget import plugin
  
log = logging.getLogger('disable_builtins')

class PluginDisableBuiltins:
    """
        Disables all builtin plugins from a feed.
    """
    def __init__(self):
        self.disabled = []

    def validator(self):
        from flexget import validator
        return validator.factory('any')
        
    def feed_start(self, feed):
        for name, info in plugin.plugins.iteritems():
            if info.builtin:
                if isinstance(feed.config['disable_builtins'], list):
                    if info.name in feed.config['disable_builtins']:
                        info.builtin = False
                        self.disabled.append(name)
                else: #disabling all builtins
                    log.debug('Disabling builtin plugin %s' % name)
                    info.builtin = False
                    self.disabled.append(name)
        
    def feed_exit(self, feed):
        for name in self.disabled:
            log.debug('Enabling builtin plugin %s' % name)
            plugin.plugins[name].builtin = True
        self.disabled = []

plugin.register_plugin(PluginDisableBuiltins, 'disable_builtins')