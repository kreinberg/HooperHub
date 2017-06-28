from datetime import date


class EntityTable(object):
    """
        Stores entities that are later read by the Interpreter. During parsing,
        entities are set based on their given tags from the Seq2Seq model and are
        stored in this class.
    """

    def __init__(self):
        """ Creates a EntityTable object and sets some defaults.
        """
        self._entity_dict = {}

        # set the defaults for EntityTable construction
        self._entity_dict['stats'] = []
        self._entity_dict['playoff_rd'] = 0 # default is regular season
        self._entity_dict['start_date'] = date(1946,11,8)
        self._entity_dict['end_date'] = date.today()
        self._entity_dict['player_name'] = None
        self._entity_dict['game_won'] = None
        self._entity_dict['home_game'] = None
        self._entity_dict['started_game'] = None
        self._entity_dict['played_for'] = None
        self._entity_dict['played_against'] = None


    def __iter__(self):
        for k,v in self._entity_dict.items():
            if v != None:
                yield k, v


    def get_stats(self):
        return self._entity_dict['stats']


    def add_stat(self, stat_entity):
        self._entity_dict['stats'].append(stat_entity)


    """ Getter and setter properties for all entity_dict pairs. """

    @property
    def player_name(self):
        return self._entity_dict['player_name']


    @player_name.setter
    def player_name(self, value):
        self._entity_dict['player_name'] = value


    @property
    def playoff_rd(self):
        return self._entity_dict['playoff_rd']


    @playoff_rd.setter
    def playoff_rd(self, value):
        self._entity_dict['playoff_rd'] = value


    @property
    def start_date(self):
        return self._entity_dict['start_date']


    @start_date.setter
    def start_date(self, value):
        self._entity_dict['start_date'] = value


    @property
    def end_date(self):
        return self._entity_dict['end_date']


    @end_date.setter
    def end_date(self, value):
        self._entity_dict['end_date'] = value


    @property
    def home_game(self):
        return self._entity_dict['home_game']


    @home_game.setter
    def home_game(self, value):
        self._entity_dict['home_game'] = value


    @property
    def started_game(self):
        return self._entity_dict['started_game']


    @started_game.setter
    def started_game(self, value):
        self._entity_dict['started_game'] = value


    @property
    def game_won(self):
        return self._entity_dict['game_won']


    @game_won.setter
    def game_won(self, value):
        self._entity_dict['game_won'] = value


    @property
    def started_game(self):
        return self._entity_dict['started_game']


    @started_game.setter
    def started_game(self, value):
        self._entity_dict['started_game'] = value


    @property
    def played_for(self):
        return self._entity_dict['played_for']


    @played_for.setter
    def played_for(self, value):
        self._entity_dict['played_for'] = value


    @property
    def played_against(self):
        return self._entity_dict['played_against']


    @played_against.setter
    def played_against(self, value):
        self._entity_dict['played_against'] = value


