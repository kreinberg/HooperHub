import inspect


class Calculator(object):
    """
        Responsible for calculating statistics given the rudimentary stats
        that were queried from the DB.
    """

    def __init__(self, rudimentary_stats):
        self.rudimentary_stats = rudimentary_stats
        self.members = inspect.getmembers(self)
        self.member_names = list(map(lambda mem: mem[0], self.members))


    def calculate(self, stat_string):
        method_name = 'calc_' + stat_string
        if method_name not in self.member_names:
            raise AttributeError
        calculation = getattr(self, method_name)
        return calculation()


    """  Time Played Calculations """

    def calc_tot_time(self):
        tot_secs_played = int(self.rudimentary_stats['sum(seconds)'])
        minutes = str(tot_secs_played//60).zfill(2)
        seconds = str(tot_secs_played%60).zfill(2)
        tot_mmss = minutes + ' minutes, ' + seconds + ' seconds'
        return "Total time played", tot_mmss


    def calc_avg_time(self):
        avg_secs_played = int(self.rudimentary_stats['avg(seconds)'])
        minutes = str(avg_secs_played//60).zfill(2)
        seconds = str(avg_secs_played%60).zfill(2)
        avg_mmss = minutes + ':' + seconds
        return "Minutes per game", avg_mmss


    """ Game Count Calculations """

    def calc_game_count(self):
        game_plyd = str(self.rudimentary_stats['count(*)'])
        return "Games played", game_plyd


    """ Field Goal Calculations """

    def calc_tot_fg(self):
        tot_fg = str(self.rudimentary_stats['sum(fg)'])
        return "Total FG", tot_fg


    def calc_avg_fg(self):
        avg_fg = str(round(self.rudimentary_stats['avg(fg)'], 2))
        return "FG per game", avg_fg


    def calc_tot_fga(self):
        tot_fga = str(self.rudimentary_stats['sum(fga)'])
        return "FG attempts", tot_fga


    def calc_avg_fga(self):
        avg_fga = str(round(self.rudimentary_stats['avg(fga)'], 2))
        return "FG attempts per game", avg_fga


    def calc_fg_pct(self):
        tot_fg = self.rudimentary_stats['sum(fg)']
        tot_fga = self.rudimentary_stats['sum(fga)']
        fg_pct = str(round((tot_fg/tot_fga)*100, 2))+'%'
        return "FG%", fg_pct


    """ 2 Point Field Goal Calculations """

    def calc_tot_fg2(self):
        tot_fg = self.rudimentary_stats['sum(fg)']
        tot_fg3 = self.rudimentary_stats['sum(fg3)']
        tot_fg2 = str(tot_fg - tot_fg3)
        return "Total 2-pt FG", tot_fg2


    def calc_avg_fg2(self):
        avg_fg = self.rudimentary_stats['avg(fg)']
        avg_fg3 = self.rudimentary_stats['avg(fg3)']
        avg_fg2 = str(round(avg_fg - avg_fg3, 2))
        return "2-pt FG per game", avg_fg2


    def calc_tot_fg2a(self):
        tot_fga = self.rudimentary_stats['sum(fga)']
        tot_fg3a = self.rudimentary_stats['sum(fg3a)']
        tot_fg2a = str(tot_fga - tot_fg3a)
        return "2-pt FG attempts", tot_fg2a


    def calc_avg_fg2a(self):
        avg_fga = self.rudimentary_stats['avg(fga)']
        avg_fg3a = self.rudimentary_stats['avg(fg3a)']
        avg_fg2a = str(round(avg_fga - avg_fg3a, 2))
        return "2-pt FG attempts per game", avg_fg2a


    def calc_fg2_pct(self):
        tot_fg = self.rudimentary_stats['sum(fg)']
        tot_fga = self.rudimentary_stats['sum(fga)']
        tot_fg3 = self.rudimentary_stats['sum(fg3)']
        tot_fg3a = self.rudimentary_stats['sum(fg3a)']
        fg2_pct = str(round(((tot_fg-tot_fg3)/(tot_fga-tot_fg3a))*100, 2))+'%'
        return "2-pt FG%", fg2_pct


    """ 3 Point Field Goal Calculations """

    def calc_tot_fg3(self):
        tot_fg3 = str(self.rudimentary_stats['sum(fg3)'])
        return "Total 3-pt FG", tot_fg3


    def calc_avg_fg3(self):
        avg_fg3 = float('%.2g' % self.rudimentary_stats['avg(fg3)'])
        return "3-pt FG per game", avg_fg3


    def calc_tot_fg3a(self):
        tot_fg3a = str(self.rudimentary_stats['sum(fg3a)'])
        return "3-pt FG attempts", tot_fg3a


    def calc_avg_fg3a(self):
        avg_fg3a = str(round(self.rudimentary_stats['avg(fg3a)'], 2))
        return "3-pt FG attempts per game", avg_fg3a


    def calc_fg3_pct(self):
        tot_fg3 = self.rudimentary_stats['sum(fg3)']
        tot_fg3a = self.rudimentary_stats['sum(fg3a)']
        fg3_pct = str(round((tot_fg3/tot_fg3a)*100, 2))+'%'
        return "3-pt FG%", fg3_pct


    """ Free Throw Calculations """

    def calc_tot_ft(self):
        tot_ft = str(self.rudimentary_stats['sum(ft)'])
        return "Total FT", tot_ft


    def calc_avg_ft(self):
        avg_ft = str(round(self.rudimentary_stats['avg(ft)'], 2))
        return "FT per game", avg_ft


    def calc_tot_fta(self):
        tot_fta = str(self.rudimentary_stats['sum(fta)'])
        return "Total FT attempts", tot_fta


    def calc_avg_fta(self):
        avg_fta = str(round(self.rudimentary_stats['avg(fta)'], 2))
        return "FT attempts per game", avg_fta


    def calc_ft_pct(self):
        tot_ft = self.rudimentary_stats['sum(ft)']
        tot_fta = self.rudimentary_stats['sum(fta)']
        ft_pct = str(round((tot_ft/tot_fta)*100, 2))+'%'
        return "FT %", ft_pct


    """ Points Calculations """

    def calc_tot_pts(self):
        tot_fg = self.rudimentary_stats['sum(fg)']
        tot_fg3 = self.rudimentary_stats['sum(fg3)']
        tot_ft = self.rudimentary_stats['sum(ft)']
        tot_fg2 = tot_fg - tot_fg3
        tot_pts = str(2*tot_fg2 + 3*tot_fg3 + tot_ft)
        return "Total points", tot_pts


    def calc_avg_pts(self):
        avg_fg = self.rudimentary_stats['avg(fg)']
        avg_fg3 = self.rudimentary_stats['avg(fg3)']
        avg_ft = self.rudimentary_stats['avg(ft)']
        avg_fg2 = avg_fg - avg_fg3
        ppg = str(round(2*avg_fg2 + 3*avg_fg3 + avg_ft, 2))
        return "PPG", ppg


    """ Rebound Calculations """

    def calc_tot_orb(self):
        tot_orb = str(self.rudimentary_stats['sum(orb)'])
        return "Total offensive rebounds", tot_orb


    def calc_avg_orb(self):
        avg_orb = str(round(self.rudimentary_stats['avg(orb)'], 2))
        return "Offensive rebounds per game", avg_orb


    def calc_tot_drb(self):
        tot_drb = self.rudimentary_stats['sum(drb)']
        return "Total defensive rebounds", tot_drb


    def calc_avg_drb(self):
        avg_drb = str(round(self.rudimentary_stats['avg(drb)'], 2))
        return "Defensive rebounds per game", avg_drb


    def calc_tot_reb(self):
        tot_orb = self.rudimentary_stats['sum(orb)']
        tot_drb = self.rudimentary_stats['sum(drb)']
        tot_reb = str(tot_orb + tot_drb)
        return "Total rebounds", tot_reb


    def calc_avg_reb(self):
        avg_orb = self.rudimentary_stats['avg(orb)']
        avg_drb = self.rudimentary_stats['avg(drb)']
        rpg = str(round(avg_orb + avg_drb, 2))
        return "Rebounds per game", rpg


    """ Assist Calculations """

    def calc_tot_ast(self):
        tot_ast = str(self.rudimentary_stats['sum(ast)'])
        return "Total assists", tot_ast


    def calc_avg_ast(self):
        avg_ast = str(round(self.rudimentary_stats['avg(ast)'], 2))
        return "Assists per game", avg_ast


    """ Block Calculations """

    def calc_tot_blk(self):
        tot_blk = str(self.rudimentary_stats['sum(blk)'])
        return "Total blocks", tot_blk


    def calc_avg_blk(self):
        avg_blk = str(round(self.rudimentary_stats['avg(blk)'], 2))
        return "Blocks per game", avg_blk


    """ Steal Calculations """

    def calc_tot_stl(self):
        tot_stl = str(self.rudimentary_stats['sum(stl)'])
        return "Total steals", tot_stl


    def calc_avg_stl(self):
        avg_stl = str(round(self.rudimentary_stats['avg(stl)'], 2))
        return "Steals per game", avg_stl


    """ Miscellaneous Calculations """

    def calc_tot_tov(self):
        tot_tov = str(self.rudimentary_stats['sum(tov)'])
        return "Total turnovers", tot_tov


    def calc_avg_tov(self):
        avg_tov = str(round(self.rudimentary_stats['avg(tov)'], 2))
        return "Turnovers per game", avg_tov


    def calc_tot_pf(self):
        tot_pf = str(self.rudimentary_stats['sum(pf)'])
        return "Total fouls", tot_pf


    def calc_avg_pf(self):
        avg_pf = str(round(self.rudimentary_stats['avg(pf)'], 2))
        return "Fouls per game", avg_pf


    """ Advanced Calculations """

    def calc_plus_min(self):
        plus_min = str(self.rudimentary_stats['sum(plus_minus)'])
        return "+/-", plus_min


    def calc_usg(self):
        usg = str(round(self.rudimentary_stats['avg(usg)'], 2))
        return "Usage rating", usg


    def calc_ortg(self):
        ortg = str(round(self.rudimentary_stats['avg(ortg)'], 2))
        return "Offensive rating", ortg


    def calc_drtg(self):
        drtg = str(round(self.rudimentary_stats['avg(drtg)'], 2))
        return "Defensive rating", drtg


    def calc_ts(self):
        tot_fg = self.rudimentary_stats['sum(fg)']
        tot_fg3 = self.rudimentary_stats['sum(fg3)']
        tot_ft = self.rudimentary_stats['sum(ft)']
        tot_pts = (tot_fg-tot_fg3) * 2 + tot_fg3 * 3 + tot_ft
        tot_fga = self.rudimentary_stats['sum(fga)']
        tot_fta = self.rudimentary_stats['sum(fta)']
        ts = str(round((tot_pts / (tot_fga + 0.44*fta))*100, 2))+'%'
        return "True Shooting", ts


