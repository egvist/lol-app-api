"""Network-free smoke tests. Run `py -m unittest test_riot_sync_offline -v`."""
import unittest
from lolapp_riot_sync import RiotClient, RiotError, PLATFORM_TO_REGION, import_match

class FakeResponse:
    status_code = 200
    text = '{}'
    headers = {}
    def __init__(self, data=None): self.data = data or {"puuid": "test"}
    def json(self): return self.data

class FakeSession:
    def __init__(self): self.headers={}; self.calls=[]
    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return FakeResponse()

class FakeCursor:
    def __init__(self, queries): self.queries=queries
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, params=()): self.queries.append((sql, params))
    def fetchone(self): return None

class FakeTransaction:
    def __enter__(self): return self
    def __exit__(self, *args): return False

class FakeConn:
    def __init__(self): self.queries=[]
    def cursor(self): return FakeCursor(self.queries)
    def transaction(self): return FakeTransaction()

class TestRiotSync(unittest.TestCase):
    def test_correct_routing(self):
        client = RiotClient('not_a_real_key', delay=0)
        client.session = FakeSession()
        client.account_by_riot_id('europe', 'Name Space', 'AB#1')
        self.assertEqual(client.session.calls[-1][0],
                         'https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Name%20Space/AB%231')
        client.league('EUW1', 'some_puuid')
        self.assertEqual(client.session.calls[-1][0],
                         'https://euw1.api.riotgames.com/lol/league/v4/entries/by-puuid/some_puuid')
        client.match_ids('europe', 'some_puuid', 420, 0, 10)
        self.assertEqual(client.session.calls[-1][1], {'queue':420,'start':0,'count':10})
        client.live('KR', 'some_puuid')
        self.assertEqual(client.session.calls[-1][0],
                         'https://kr.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/some_puuid')

    def test_match_has_ten_players_and_two_teams(self):
        db=FakeConn()
        example = {
            'metadata': {'matchId':'EUW1_1234567890'},
            'info': {
                'queueId': 420, 'gameMode': 'CLASSIC', 'gameVersion': '16.20.1',
                'gameStartTimestamp': 1790000000000,'gameDuration': 1800, 'mapId':11,
                'teams':[{'teamId':100, 'win':True,'objectives':{'dragon':{'kills':2}}},
                         {'teamId':200, 'win':False,'objectives':{'dragon':{'kills':1}}}],
                'participants': [
                    {'participantId':i, 'teamId':100 if i<=5 else 200, 'puuid':f'puuid_{i}',
                     'championId':i, 'teamPosition':'MIDDLE', 'win':i<=5,
                     'kills':1, 'deaths':2, 'assists':3} for i in range(1,11)]
            }
        }
        self.assertTrue(import_match(db, example))
        match_inserts=sum('INSERT INTO matches' in sql for sql,_ in db.queries)
        team_inserts=sum('INSERT INTO match_teams' in sql for sql,_ in db.queries)
        player_inserts=sum('INSERT INTO match_participants' in sql for sql,_ in db.queries)
        self.assertEqual((match_inserts,team_inserts,player_inserts),(1,2,10))

    def test_custom_queue_skipped(self):
        conn=FakeConn()
        self.assertFalse(import_match(conn, {'metadata':{'matchId':'EUW1_0'},'info':{'queueId':0}}))
        self.assertEqual(conn.queries, [])

if __name__ == '__main__':
    unittest.main()
