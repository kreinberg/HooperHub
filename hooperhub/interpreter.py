import os
import pickle
import datetime
import psycopg2 as psql

from hooperhub.util import EntityTable, Calculator


class Interpreter(object):
    """ Given an EntityTable object, this reads the given entities and makes
        the query to the DB accordingly. The interpreter also calls from a
        Calculator object to quantify the statistics that were queried.
    """

    def __init__(self,
                entity_table,
                stat_path,
                PG_HOST,
                PG_PORT,
                PG_DBNAME,
                PG_USER):
        """ Create the Interpreter and load necessary information.
            Args:
                entity_table: an EntityTable object containing all queried
                    statistics and conditions of the query.
                PG_HOST: the PostgreSQL hostname of the DB.
                PG_PORT: the PostgreSQL port number of the DB.
                PG_DBNAME: the PostgreSQL dbname of the DB.
                PG_USER: the PostgreSQL username of the DB.
        """
        self._entity_table = entity_table

        # from settings.py
        self.conn = psql.connect(host = PG_HOST,
                                 port = PG_PORT,
                                 dbname  = PG_DBNAME,
                                 user = PG_USER)
        self.cursor = self.conn.cursor()

        # stat_recipes maps stat entities with needed elements to calculate
        # it. e.g. PPG entity would match with [fg, fg3, and ft]
        stat_recipes_path = stat_path
        self.stat_recipes = pickle.load(open(stat_recipes_path, 'rb'))

        self._base_query = """ 
            SELECT ({cols}) FROM performance WHERE {conds};
            """


    def close_psql_connection(self):
        """ Closes the PostgreSQL cursor and connection.
        """
        self.cursor.close()
        self.conn.close()


    def _get_player_id(self, player_name):
        """ Selects the player_id for a given player's name.
            Args:
                player_name: The name of the player in the EntityTable
            Returns:
                The player id associated with given player name
        """
        select_p_id_query = """ SELECT player_id FROM player WHERE name=%s; """
        self.cursor.execute(select_p_id_query, (player_name,))
        return self.cursor.fetchone()[0]


    def _get_team_abbr(self, team_id):
        """ Selects the team_abbr with the associated team_id
            Args:
                team_id: The team id to be queried
            Returns:
                The team's abbreviation with given team id
        """
        select_team_abbr_query = """ SELECT abbr FROM team WHERE 
                                        team_id=%s; """
        self.cursor.execute(select_team_abbr_query, (team_id,))
        return self.cursor.fetchone()[0]

    def _get_needed_columns(self, stat_entities):
        """ Finds the needed columns to be queried from the DB. It returns
            a set to prevent from querying specific stats twice
            e.g., getting both PPG and FT percentage both require FT from DB,
            but we will only need to query for it once and can reuse it
            Args:
                stat_entities: a list of all the stats taken from the
                    EntityTable
            Returns:
                A set containing all necessary columns to calculate all
                    queried statistics
        """
        columns = set()
        for stat in stat_entities:
            recipe = self.stat_recipes[stat]
            columns = columns.union(set(recipe))
        return columns


    def _aggregate_conditions(self):
        """ Function that forms the condition strings and collects all
            condition tokens for interpretation.
            Returns:
                A dictionary of token names with their given values and a
                string containing the end of the PostgreSQL query that will
                be executed to retrieve the requested statistics.

        """
        cond_tok = {}
        cond_str = ""

        # mandate that a player_name entity exists or raise exception
        if not self._entity_table.player_name:
            raise KeyError
        player_name = self._entity_table.player_name
        cond_tok["Player"] = player_name
        player_id = self._get_player_id(player_name)
        cond_str += "player_id={plyr_id}".format(plyr_id = player_id)

        # playoff_rd condition
        playoff_str = " AND playoff_rd"
        if self._entity_table.playoff_rd == 0:
            playoff_str += "=0"
        else:
            cond_tok["Playoffs?"] = "Yes"
            playoff_str += ">0"
        cond_str += playoff_str

        # game_won condition
        if self._entity_table.game_won != None:
            game_won_str = " AND win_margin"
            if self._entity_table.game_won:
                cond_tok["Win/Loss"] = "Win"
                game_won_str += ">0"
            else:
                cond_tok["Win/Loss"] = "Loss"
                game_won_str += "<0"
            cond_str += game_won_str

        # home_game condition
        if self._entity_table.home_game != None:
            home_game_str = " AND home="
            if self._entity_table.home_game:
                cond_tok["Home/Away"] = "Home"
                home_game_str += "true"
            else:
                cond_tok["Home/Away"] = "Away"
                home_game_str += "false"
            cond_str += home_game_str

        # started_game condition
        if self._entity_table.started_game != None:
            started_game_str = " AND started="
            if self._entity_table.started_game:
                cond_tok["Started?"] = "Yes"
                started_game_str += "true"
            else:
                cond_tok["Started?"] = "No"
                started_game_str += "false"
            cond_str += started_game_str

        # played_for condition
        if self._entity_table.played_for:
            team_id = self._entity_table.played_for
            team_abbr = self._get_team_abbr(team_id)
            cond_tok["Played for"] = team_abbr
            cond_str += " AND team={}".format(str(team_id))

        # played_against condition
        if self._entity_table.played_against:
            opp_team_id = self._entity_table.played_against
            opp_team_abbr = self._get_team_abbr(opp_team_id)
            cond_tok["Played against"] = opp_team_abbr
            cond_str += " AND opp={}".format(str(opp_team_id))

        # date condition
        if self._entity_table.start_date != datetime.date(1946,11,8):
            cond_tok["After"] = str(self._entity_table.start_date)
        if self._entity_table.end_date != datetime.date.today():
            cond_tok["Before"] = str(self._entity_table.end_date)
        cond_str += " AND game_date>%s AND game_date<%s"

        # change After/Before strings with "Season" if applicable
        start_year = self._entity_table.start_date.year
        end_year = self._entity_table.end_date.year
        if (end_year-start_year == 1 and
            self._entity_table.start_date.month == 10 and
            self._entity_table.start_date.day == 1 and
            self._entity_table.end_date.month == 7 and
            self._entity_table.end_date.day == 1):
            del cond_tok["After"]
            del cond_tok["Before"]
            cond_tok["Season"] = str(end_year)

        return cond_tok, cond_str

    def __call__(self):
        """ The "main" function of the Interpreter.
        Args:
            entity_table: a EntityTable object that contains all of entities 
                that were parsed by the Lexer.
        Returns:
            A dictionary containing all of the parsed entities and a dictionary
            containing calculated results, all contained in a 2-tuple.
        """
        stat_entities = self._entity_table.get_stats()

        # add default statistics if none exist
        if stat_entities == []:
            stat_entities.extend(['avg_time',
                                  'avg_pts',
                                  'avg_reb',
                                  'avg_ast',
                                  'game_count'])

        # retrieve required columns for the query
        columns = ','.join(self._get_needed_columns(stat_entities))

        # create the condition string and a dictionary of all the conditions
        condition_entitys, conditions_str = self._aggregate_conditions()

        query = self._base_query.format(cols = columns, conds = conditions_str)
        start_date = self._entity_table.start_date
        end_date = self._entity_table.end_date
        self.cursor.execute(query, (start_date, end_date))
        res = self.cursor.fetchone()[0]
        if type(res) != str:
            results = (res,)
        else:
            results = eval(res)
        # pass all of the query results into a Calculator
        result_entitys = {}
        rudimentary_stats = dict(zip(columns.split(','), results))
        calc = Calculator(rudimentary_stats)
        for stat in stat_entities:
            result_pair = calc.calculate(stat)
            result_entitys.update([result_pair])

        return condition_entitys, result_entitys


