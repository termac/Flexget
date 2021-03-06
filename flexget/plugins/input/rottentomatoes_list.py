from __future__ import unicode_literals, division, absolute_import
import logging
from flexget.plugin import register_plugin, DependencyError
from flexget.utils.cached_input import cached
from flexget.entry import Entry

try:
        from flexget.plugins.api_rottentomatoes import lists
except ImportError:
        raise DependencyError(issued_by='rottentomatoes_lookup', missing='api_rottentomatoes',
                              message='rottentomatoes_lookup requires the `api_rottentomatoes` plugin')

log = logging.getLogger('rottentomatoes_list')


class RottenTomatoesList(object):
    """
        Emits an entry for each movie in a Rotten Tomatoes list.

        Configuration:

        dvds:
          - top_rentals
          - upcoming

        movies:
          - box_office

        Possible lists are
          * dvds: top_rentals, current_releases, new_releases, upcoming
          * movies: box_office, in_theaters, opening, upcoming

    """

    def __init__(self):
        # We could pull these from the API through lists.json but that's extra web/API key usage
        self.dvd_lists = ['top_rentals', 'current_releases', 'new_releases', 'upcoming']
        self.movie_lists = ['box_office', 'in_theaters', 'opening', 'upcoming']

    def validator(self):
        from flexget import validator
        root = validator.factory('dict')
        root.accept('list', key='dvds').accept('choice').accept_choices(self.dvd_lists)
        root.accept('list', key='movies').accept('choice').accept_choices(self.movie_lists)
        return root

    @cached('rottentomatoes_list', persist='2 hours')
    def on_task_input(self, task, config):
        entries = []
        for l_type, l_names in config.items():
            for l_name in l_names:
                results = lists(list_type=l_type, list_name=l_name)
                if results:
                    for movie in results['movies']:
                        if filter(lambda entry: movie['title'] == entry.get('title'), entries):
                            continue
                        imdb_id = movie.get('alternate_ids', {}).get('imdb')
                        if imdb_id:
                            imdb_id = 'tt' + str(imdb_id)
                        entries.append(Entry(title=movie['title'], rt_id=movie['id'],
                            imdb_id=imdb_id,
                            rt_name=movie['title'],
                            url=movie['links']['alternate']))
                else:
                    log.critical('Failed to fetch Rotten tomatoes %s list: %s. List doesn\'t exist?' %
                            (l_type, l_name))
        return entries

register_plugin(RottenTomatoesList, 'rottentomatoes_list', api_ver=2)
