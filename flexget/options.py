from optparse import OptionParser as OptParser, SUPPRESS_HELP
import logging

class OptionParser(OptParser):
    def __init__(self, unit_test=False):
        OptParser.__init__(self)

        self._unit_test = unit_test

        self.add_option('--log-start', action='store_true', dest='log_start', default=0,
                          help='Add FlexGet executions into a log.')
        self.add_option('--test', action='store_true', dest='test', default=0,
                          help='Verbose what would happend on normal execution.')
        self.add_option('--check', action='store_true', dest='validate', default=0,
                          help='Validate configuration file and print errors.')
        self.add_option('--learn', action='store_true', dest='learn', default=0,
                          help='Matches are not downloaded but will be skipped in the future.')
        self.add_option('--feed', action='store', dest='onlyfeed', default=None,
                          help='Run only specified feed.')
        self.add_option('--no-cache', action='store_true', dest='nocache', default=0,
                          help='Disable caches. Works only in plugins that have explicit support.')
        self.add_option('--reset', action='store_true', dest='reset', default=0,
                          help='Forgets everything that has been done and learns current matches.')
        self.add_option('--doc', action='store', dest='doc',
                          help='Display plugin documentation (example: --doc patterns). See --list.')
        self.add_option('--list', action='store_true', dest='list', default=0,
                          help='List all available plugins.')
        self.add_option('--failed', action='store_true', dest='failed', default=0,
                          help='List recently failed entries.')
        self.add_option('--clear', action='store_true', dest='clear_failed', default=0,
                          help='Clear recently failed list.')
        self.add_option('-c', action='store', dest='config', default='config.yml',
                          help='Specify configuration file. Default is config.yml')
        self.add_option('-v', action='store_true', dest='details', default=0,
                          help='Verbose more process information.')
        self.add_option('--cron', action='store_true', dest='quiet', default=False,
                          help='Disables stdout and stderr output, log file used. Reduces logging level slightly.')

        self.add_option('--experimental', action='store_true', dest='experimental', default=0,
                          help=SUPPRESS_HELP)
        self.add_option('--debug', action='callback', callback=self._debug_callback, dest='debug',
                        help=SUPPRESS_HELP)
        self.add_option('--debug-all', action='callback', callback=self._debug_callback, dest='debug_all',
                        help=SUPPRESS_HELP)
        self.add_option('--loglevel', action='store', type='choice', default='info', dest='loglevel',
                        choices=['none', 'critical', 'error', 'warning', 'info', 'debug', 'debugall'],
                        help=SUPPRESS_HELP)
        self.add_option('--debug-sql', action='store_true', dest='debug_sql', default=False,
                          help=SUPPRESS_HELP)
        self.add_option('--validate', action='store_true', dest='validate', default=0,
                          help=SUPPRESS_HELP)
        self.add_option('--verbosity', action='store_true', dest='crap', default=0,
                          help=SUPPRESS_HELP)

        self.add_option('--migrate', action='store', dest='migrate', default=None,
                          help=SUPPRESS_HELP)

        # provides backward compatibility to --cron and -d
        self.add_option('-q', '--quiet', action='store_true', dest='quiet', default=False,
                          help=SUPPRESS_HELP)
        self.add_option('-d', action='store_true', dest='details', default=0,
                          help=SUPPRESS_HELP)

    def parse_args(self):
        result = OptParser.parse_args(self, self._unit_test and ['flexget', '--reset'] or None)
        options = result[0]
        if options.test and options.learn:
            self.error('--test and --learn are mutually exclusive')
            
        if options.test and options.reset:
            self.error('--test and --reset are mutually exclusive')

        # reset and migrate should be executed with learn
        if (options.reset and not self._unit_test) or options.migrate:
            options.learn = True

        return result

    def _debug_callback(self, option, opt, value, parser):
        setattr(parser.values, option.dest, 1)
        if option.dest == 'debug':
            setattr(parser.values, 'loglevel', 'debug')
        elif option.dest == 'debug_all':
            setattr(parser.values, 'debug', 1)
            setattr(parser.values, 'loglevel', 'debugall')