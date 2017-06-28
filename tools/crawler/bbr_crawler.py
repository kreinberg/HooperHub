import bs4
import threading
import datetime
import psycopg2 as psql

from urllib.request import urlopen
from urllib.error import HTTPError

from time import sleep, time
from collections import defaultdict

# includes all of the psql queries and the Performance namedtuple
from crawler_utils import *


class BBR_Crawler(object):
    """ A web crawler and scraper for basketball-reference.com. It periodically
        crawls through the site scraping new gamelog data for each player in
        the player table. DB connection is required to run. Many details of the
        crawler are obfuscated from this implementation for crawling etiquette
        purposes. All statistics in this app are provided thanks to
        basketball-reference.com
    """

    def __init__(self, base_url, dbname):
        """ Constructs the crawler.
            Args:
                base_url: The url for the Basketball Reference index page.
                dbname: Name of the database where data will be stored.

        """
        self.base_url = base_url
        # psycopg2 connection and cursor
        self.conn = psql.connect(host = PG_HOST,
                                 port = PG_PORT,
                                 dbname = PG_DBNAME,
                                 user = PG_USER)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()
        # keeps track of the last urlopen request
        self.last_req = time()


    def print_ts(self, sentence):
        """ Prints any log information with a timestamp.
            Args:
                sentence: The sentence that will be printed next to the
                    timestamp.
        """
        ts = (datetime.datetime.fromtimestamp(time()).strftime('[%Y-%m-%d %H:%M:%S]: '))
        print(ts+sentence)


    def get_soup(self, url):
        """ Creates and returns a BeautifulSoup object. It will make sure
                that URL requests are throttled at a minimum of 3 seconds.
            Args:
                url: The url that will be requested.
            Returns:
                The BeautifulSoup object that can be scraped.
        """
        html = ''

        # ensure three second delay between requests
        dur = time() - self.last_req
        sleep((3 - dur) if (dur < 3) else 0)

        self.print_ts("Opening URL: "+url)
        try: 
            html = urlopen(url).read()
        except HTTPError:
            self.print_ts("Could not open URL: "+url)
        finally:
            # update the last request time regardless of failure
            self.last_req = time()

        soup = bs4.BeautifulSoup(html, 'html.parser')
        return soup


    def get_playoff_teams(self, post_season_soup):
        """ Creates a dictionary that maps the playoff round to a team id.
            Args:
                post_season_soup: A BeautifulSoup object with an html table
                    containing all the playoff data.
            Returns:
                A dictionary with keys as team names and values as the
                playoff round.
        """
        post_season_game_rows = post_season_soup.findAll('tr')

        rd = 1
        prev_team = ''
        playoff_dict = defaultdict(int)
        for game_row in post_season_game_rows:
            opponent = game_row.find('td', {'data-stat': 'opp_id'})
            # skip any row that doesn't have the tag 'opp_id'
            if not opponent:
                continue
            opponent = opponent.string

            if opponent != prev_team:
                playoff_dict[opponent] = rd
                rd += 1
                prev_team = opponent

        return playoff_dict


    def scrape_season(self, player_id, player_url, season):
        """
            Args:
                player_id: The id for the player being scraped.
                season: The season that is being scraped. It is concatenated
                    to the gamelog_url to make the URL request and get the
                    gamelog soups
            Returns:
                A list of Performance objects containing all gamelog data
                for the given season.
        """
        self.cursor.execute(select_last_played, (player_id,))
        last_played = self.cursor.fetchone()[0]

        basic_gamelog_url = self.base_url+player_url+"/gamelog/"+season
        basic_gamelog_soup = self.get_soup(basic_gamelog_url)
        basic_data = self.scrape_gamelog(player_id,
                                         basic_gamelog_soup)

        adv_gamelog_url = self.base_url+player_url+"/gamelog-advanced/"+season
        adv_gamelog_soup = self.get_soup(adv_gamelog_url)
        adv_data = self.scrape_gamelog(player_id,
                                       adv_gamelog_soup,
                                       advanced=True)

        # adds both basic and advanced data tuples for each game
        total_gl_data = list(map(lambda x,y: x+y, basic_data, adv_data))
        season_data = []
        for game in total_gl_data:
            season_data.append(Performance(*game))
        return season_data


    def scrape_gamelog(self, player_id, soup, advanced=False):
        """ Scraped a gamelog for a given player. It can be regular stats or
            advanced.
            Args:
                player_id: The id for the given player to be scraped.
                soup: the BeautifulSoup object containing all the gamelog data.
                advanced: A boolean that when true scraped the advanced
                    gamelog stats.
            Returns:
                A list of gamelog data which are stored as tuples.
        """
        gl_data = []

        reg_season_div_id = 'all_pgl_basic'
        post_season_div_id = 'all_pgl_basic_playoffs'
        if advanced:
            reg_season_div_id = 'all_pgl_advanced'
            post_season_div_id = 'all_pgl_advanced_playoffs'

        reg_season_div = soup.find('div', id=reg_season_div_id)
        if reg_season_div:
            reg_season_table = reg_season_div.find('tbody')
            reg_season_game_rows = reg_season_table.findAll('tr', id=True)
            for game_row in reg_season_game_rows:
                gl_data.append(self.scrape_statline(player_id,
                                                    game_row,
                                                    defaultdict(int),
                                                    advanced))

        post_season_div = soup.find('div', id=post_season_div_id)
        if post_season_div:
            # for some reason, the HTML for playoff data is in a comment...
            # so we'll parse that comment and create a new BS4 object out
            # of it
            post_season_text = post_season_div.find(
                               text = lambda t: isinstance(t, bs4.Comment))
            post_season_soup = bs4.BeautifulSoup(post_season_text,
                                                 'html.parser')
            post_season_table = post_season_soup.find('tbody')
            post_season_dict = self.get_playoff_teams(post_season_table)
            post_season_game_rows = post_season_table.findAll('tr', id=True)
            for game_row in post_season_game_rows:
                gl_data.append(self.scrape_statline(player_id,
                                                    game_row,
                                                    post_season_dict,
                                                    advanced))

        return gl_data


    def get_stat(self, stat_name, game_row):
        """ Gets the stat for the given name from the statline row.
            Args:
                stat_name: The name of the stat that will be scraped.
                game_row: The soup that will be scraped from.
            Returns:
                A string that represents the stat value.
        """
        stat = game_row.find('td', {'data-stat': stat_name})
        if stat != None:
            stat = stat.string
        return stat


    def get_team_id(self, team_str):
        """ Gets the team id and also takes care of any ambiguous team
            abbreviations.
            Args:
                team_str: The team abbreviation.
            Returns:
                The team id associated with team_str.
        """
        # change team abbreviation to one that exists in database
        if team_str == "CHO" or team_str == "CHH":
            team_str = "CHA"
        if team_str == "NOH" or team_str == "NOK":
            team_str = "NOP"
        if team_str == "NJN":
            team_str = "BRK"
        if team_str == "WSB":
            team_str = "WAS"
        if team_str == "VAN":
            team_str = "MEM"
        if team_str == "SEA":
            team_str = "OKC"

        self.cursor.execute(select_team_id, (team_str.lower(),))
        team_id = self.cursor.fetchone()

        if not team_id:
            self.cursor.execute(insert_team_id, (team_str,))
            self.cursor.execute(select_team_id, (team_str,))
            team_id = self.cursor.fetchone()

        return team_id[0]


    def scrape_statline(self, player_id, statline, playoff_dict, adv):
        """ Responsible for scraping the statline soup.
            Args:
                player_id: The id for the player that is being scraped.
                statline: The BeautifulSoup object containing the row of all
                    the player stats.
                playoff_dict: The dictionary that maps team's to playoff round.
                    It is an empty defaultdict for regular season statlines.
                adv: A boolean that when true scrapes the advanced stats.
            Returns:
                A tuple containing all stat values in the table row.
        """
        # adv stats
        if adv:
            usg  = self.get_stat('usg_pct', statline)
            ortg = self.get_stat('off_rtg', statline)
            drtg = self.get_stat('def_rtg', statline)

            return (usg, ortg, drtg)

        # basic stats
        game_date   = self.get_stat('date_game', statline)
        game_result = self.get_stat('game_result', statline)
        location    = self.get_stat('game_location', statline)
        team        = self.get_stat('team_id', statline)
        opp         = self.get_stat('opp_id', statline)
        started     = self.get_stat('gs', statline)
        time_played = self.get_stat('mp', statline)
        fg          = self.get_stat('fg', statline)
        fga         = self.get_stat('fga', statline)
        fg3         = self.get_stat('fg3', statline)
        fg3a        = self.get_stat('fg3a', statline)
        ft          = self.get_stat('ft', statline)
        fta         = self.get_stat('fta', statline)
        orb         = self.get_stat('orb', statline)
        drb         = self.get_stat('drb', statline)
        ast         = self.get_stat('ast', statline)
        stl         = self.get_stat('stl', statline)
        blk         = self.get_stat('blk', statline)
        tov         = self.get_stat('tov', statline)
        pf          = self.get_stat('pf', statline)
        plus_minus  = self.get_stat('plus_minus', statline)

        # get playoff_rd (e.g. 0 = regular season, 4 = finals)
        playoff_rd = playoff_dict[opp]
        # convert MM:SS to seconds
        if not time_played:
            mmss = [0,0]
        else:
            mmss = list(map(int, time_played.split(':')))
        seconds = mmss[0]*60 +mmss[1]
        # convert date string to datetime object
        date = datetime.date(*tuple(map(int, game_date.split('-'))))
        # convert started (0 or 1) to a boolean
        started = bool(int(started))
        # convert game_result string (e.g. "L (-15)") into an int (-15)
        win_margin = eval(game_result[game_result.find('('):])
        # convert location ('@' or '') to a boolean
        home = False
        if location == None or location == '':
            home = True
        # convert team abbrevations to their corresponding team_id in the DB
        team_id = self.get_team_id(team)
        opp_id = self.get_team_id(opp)

        return (player_id, date, playoff_rd, win_margin, home, team_id, opp_id,
                started, seconds, fg, fga, fg3, fg3a, ft, fta, orb, drb,ast, 
                stl, blk, tov, pf, plus_minus)


    def update_performances(self, performance_data, player_id):
        """ Inserts new performance into performance table and updates the
            last_played date in the player table.
            Args:
                performance_data: The columns to be updated in performances.
                player_id: The id for the player who will be updated.
        """
        self.cursor.execute(select_last_played, (player_id,))
        last_played = self.cursor.fetchone()[0]

        self.cursor.execute(select_player_name, (player_id,))
        player_name = self.cursor.fetchone()[0]

        successful_insert_count = 0
        for p in performance_data:
            if last_played == None or last_played < p.game_date:
                # insert into performance table
                self.cursor.execute(insert_performance, p)
                # update last played date for player
                self.cursor.execute(update_last_played, (p.game_date, player_id))
                successful_insert_count += 1

        self.print_ts("Successfully inserted {} performances for {}".format(
                      successful_insert_count, player_name))


    def crawl(self, complete_crawl=False, start_id=1):
        """ Begins the crawling process.
            Args:
                complete_crawl: boolean that when True will crawl player data
                    from the beginning of their rookie year. This is only
                    necessary when you are crawling a player's information for
                    the first time.
                start_id: The first player id to crawl for. This is useful if
                    the crawler crashed or stops in the middle of scraping a
                    player so we don't have to crawl from the beginning.
        """
        self.cursor.execute(select_all_players)
        players = self.cursor.fetchall()

        now = datetime.datetime.now()
        current_season = now.year
        # update the new season every September
        if now.month > 8:
            current_season += 1

        # player tuple: (player_id, name, url, rookie_year, last_played)
        for player in players:
            # start_id is a player_id of where we want to start scraping
            # this allows us to skip players if we know they are up to date
            # and can save us time
            if player[0] < start_id:
                continue
            player_data = []
            start_season = current_season
            if complete_crawl:
                # start at player's rookie season for complete crawl
                start_season = player[3]

            for season in range(start_season, current_season+1):
                player_data.extend(self.scrape_season(player[0],
                                                      player[2],
                                                      str(season)))

            self.update_performances(player_data, player[0])


        self.cursor.close()
        self.conn.close()


