from __future__ import unicode_literals, division, absolute_import
import logging
import re
import datetime
from copy import copy
from collections import defaultdict

from flexget.task import Task
from flexget.entry import Entry
from flexget.plugin import register_plugin, plugins as all_plugins, get_plugin_by_name, phase_methods

log = logging.getLogger('if')


def safer_eval(statement, locals):
    """A safer eval function. Does not allow __ or try statements, only includes certain 'safe' builtins."""
    allowed_builtins = ['True', 'False', 'str', 'unicode', 'int', 'float', 'len', 'any', 'all', 'sorted']
    for name in allowed_builtins:
        locals[name] = globals()['__builtins__'].get(name)
    if re.search(r'__|try\s*:|lambda', statement):
        raise ValueError('`__`, lambda or try blocks not allowed in if statements.')
    return eval(statement, {'__builtins__': None}, locals)


class FilterIf(object):
    """Can run actions on entries that satisfy a given condition.

    Actions include accept, reject, and fail, as well as the ability to run other filter plugins on the entries."""

    def __init__(self):
        self.task_phases = {}

    def validator(self):
        from flexget import validator
        root = validator.factory('list')
        key_validator = validator.factory('regexp_match',
                                          message='If statements cannot contain `__`,  `try` or `lambda` statements')
        key_validator.reject(r'.*?(__|try\s*:|lambda)')
        key_validator.accept('.')
        action = root.accept('dict').accept_valid_keys('root', key_validator=key_validator)
        action.accept('choice').accept_choices(['accept', 'reject', 'fail'])
        filter_action = action.accept('dict')
        # Build a dict validator that accepts all api > 2 plugins except input plugins.
        for plugin in all_plugins.itervalues():
            if plugin.api_ver > 1 and hasattr(plugin.instance, 'validator') and 'input' not in plugin.phase_handlers:
                filter_action.accept(plugin.instance.validator, key=plugin.name)
        return root

    def on_process_start(self, task, config):
        """Divide the config into parts based on which phase they need to run on."""
        phase_dict = self.task_phases[task.name] = defaultdict(lambda: [])
        for item in config:
            action = item.values()[0]
            if isinstance(action, basestring):
                phase_dict['filter'].append(item)
            else:
                for plugin_name, plugin_config in action.iteritems():
                    plugin = get_plugin_by_name(plugin_name)
                    for phase in plugin.phase_handlers:
                        if phase == 'process_start':
                            # If plugin has a process_start handler, run it now unconditionally
                            try:
                                plugin.phase_handlers[phase](task, plugin_config)
                            except TypeError:
                                # Print to debug, as validator will show user error message
                                log.debug('Cannot run api < 2 plugins.')
                        else:
                            phase_dict[phase].append(item)

    def check_condition(self, condition, entry):
        """Checks if a given `entry` passes `condition`"""
        # Make entry fields and other utilities available in the eval namespace
        # We need our namespace to be an Entry instance for lazy loading to work
        eval_locals = copy(entry)
        eval_locals.update({'has_field': lambda f: f in entry,
                            'timedelta': datetime.timedelta,
                            'now': datetime.datetime.now()})
        try:
            # Restrict eval namespace to have no globals and locals only from eval_locals
            passed = safer_eval(condition, eval_locals)
            if passed:
                log.debug('%s matched requirement %s' % (entry['title'], condition))
            return passed
        except NameError as e:
            # Extract the name that did not exist
            missing_field = e.message.split('\'')[1]
            log.debug('%s does not contain the field %s' % (entry['title'], missing_field))
        except Exception as e:
            log.error('Error occurred in if statement: %r' % e)

    def __getattr__(self, item):
        """Provides handlers for all phases except input and entry phases."""
        for phase, method in phase_methods.iteritems():
            # TODO: Deal with entry phases
            if item == method and phase not in ['accept', 'reject', 'fail', 'input']:
                break
        else:
            raise AttributeError(item)

        def handle_phase(task, config):
            if task.name not in self.task_phases:
                log.debug('No config dict was generated for this task.')
                return
            entry_actions = {
                'accept': Entry.accept,
                'reject': Entry.reject,
                'fail': Entry.fail}
            for item in self.task_phases[task.name][phase]:
                requirement, action = item.items()[0]
                passed_entries = [e for e in task.entries if self.check_condition(requirement, e)]
                if passed_entries:
                    if isinstance(action, basestring):
                        # Simple entry action (accept, reject or fail) was specified as a string
                        for entry in passed_entries:
                            entry_actions[action](entry, 'Matched requirement: %s' % requirement)
                    else:
                        # Other plugins were specified to run on this entry
                        fake_task = Task(task.manager, task.name, task.config)
                        fake_task.session = task.session
                        # This entry still belongs to our feed, accept/reject etc. will carry through.
                        fake_task.all_entries[:] = passed_entries

                        try:
                            for plugin_name, plugin_config in action.iteritems():
                                plugin = get_plugin_by_name(plugin_name)
                                method = plugin.phase_handlers[phase]
                                method(fake_task, plugin_config)
                        except Exception:
                            raise

        handle_phase.priority = 80
        return handle_phase


register_plugin(FilterIf, 'if', api_ver=2)
