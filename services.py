from pocketbase import PocketBase
from dotenv import load_dotenv
import os

load_dotenv()


class Db():
    def __init__(self):
        self.pb = PocketBase(os.environ['pb'])

    def active_seesion(self) -> bool:
        return True if self.pb.collection('kulhun').get_list(1, 20,
                                                             {"filter": 'completed = false'}).total_items > 0 else False

    def no_players(self) -> int:
        return self.pb.collection('team').get_list(1, 20, {"filter": 'active = true'}).total_items

    def max_players(self) -> int:
        row = self.pb.collection('kulhun').get_list(1, 20, {"filter": 'completed = false'})
        return row.items[0].max_players if row.total_items > 0 else 0

    def max_reserved(self) -> int:
        row = self.pb.collection('kulhun').get_list(1, 20, {"filter": 'completed = false'})
        return row.items[0].max_reserves if row.total_items > 0 else 0

    # mark all players attented for current seeion
    def all_attended(self):
        players = self.pb.collection('team').get_list(1, 20, {"filter": 'active = true'})
        for player in players.items:
            self.pb.collection('team').update(player.id, {"active": False, "attended": True})

            # update player info total_attended from player where tid = tid
            tid = self.pb.collection('team').get_one(player.id).tid
            player = self.pb.collection('players').get_list(1, 20, {"filter": f'tid = {tid}'}).items
            self.pb.collection('players').update(player[0].id, {"total_attended": player[0].total_attended + 1})

    def create_kulhun(self, tid: int, desc: str, mid: int, mp=14, mr=3) -> str:
        # check for on goin polling
        try:
            p_sess = self.pb.collection('kulhun').get_list(1, 20, {"filter": 'completed = false'})
            print('sess', p_sess.total_items)

            # storing kulhun
            if p_sess.total_items == 0:
                body = {
                    "tid": tid,
                    "description": desc,
                    "max_players": mp,
                    "max_reserves": mr,
                    "completed": False,
                    "message_id": mid,
                    "player": self.pb.collection('players').get_first_list_item(filter=f'tid = {tid}').id
                }
                kulhun = self.pb.collection('kulhun').create(body)
                return kulhun.id
            else:
                return '0'
        except Exception as e:
            print("Error in some where")
            print(e)

    def on_list(self, tid):
        p = self.pb.collection('team').get_list(1, 20, {"filter": f'tid = {tid} && active = true'})
        return p.total_items
        # return 0

    def add_to_team(self, tid, on_team):
        try:
            player =  self.pb.collection('players').get_first_list_item(filter=f'tid = {tid}')
            print(player.id)
            body = {
                "tid": tid,
                "active": True,
                "attended": False,
                "on_team": on_team,
                "kulhun": self.pb.collection('kulhun').get_first_list_item(filter='completed = true').id,
                "player": player.id

            }

            self.pb.collection('team').create(body)
            # update player info total_enrolled from player where tid = tid
            # player = self.pb.collection('players').get_list(1, 20, {"filter": f'tid = {tid}'}).items
            self.pb.collection('players').update(player.id, {"total_enrolled": player.total_enrolled+1})
            return True
        except Exception as e:
            print(f'In db uodate error {e}')
            return False

    def insert_new_player(self, tid, name):
        # insert new player to table player
        print(name)
        try:
            body = {
                "tid": tid,
                "t_name": str(name),
                "u_name": str(name),
            }
            self.pb.collection('players').create(body)
            return True
        except Exception as e:
            print(e)
            return False

    def team_list(self) -> str:
        # players = self.pb.collection('team').get_list(1, 20, {"filter": 'active = true && on_team = true'})
        # reserved = self.pb.collection('team').get_list(1, 20, {"filter": 'active = true && on_team = false'})
        team_list = ''
        # Fetch team members
        players = self.pb.collection('team').get_list(
            page=1,
            per_page=20,
            query_params={
                "filter": 'active = true && on_team = true',
                "expand": 'player'
            }
        )
        reserved = self.pb.collection('team').get_list(
            page=1,
            per_page=20,
            query_params={
                "filter": 'active = true && on_team = false',
                "expand": 'player'
            }
        )
        for i, playe in enumerate(players.items):
            name = playe.expand['player'].t_name
            team_list += f"{i + 1}. {name}\n"

        if reserved.total_items > 0:
            team_list += f"-------------------\nRESERVED\n-------------------\n"
            for i, res in enumerate(reserved.items):
                name = res.expand['player'].t_name
                team_list += f"{i + 1}. {name}\n"
        return team_list

    # updates
    # mark player off the list
    def off_list(self, tid):
        try:
            players = self.pb.collection('team').get_list(1, 20, {"filter": f'active = true && tid={tid}'})
            reserved = self.pb.collection('team').get_list(1, 20, {"filter": 'active = true && on_team = false'})
            # self.pb.collection('team').update(players.items[0].id, {"active": False})
            self.pb.collection('team').delete(players.items[0].id)
            if reserved.total_items > 0:
                self.pb.collection('team').update(reserved.items[0].id, {"on_team": True})

            # update player info total_enrolled from player where tid = tid
            player = self.pb.collection('players').get_list(1, 20, {"filter": f'tid = {tid}'}).items
            self.pb.collection('players').update(player[0].id, {"total_enrolled": player[0].total_enrolled - 1})
            return True
        except Exception as e:
            print(e)
            return False

        # get list of gid from groups
    def get_gids(self) -> list[int]:
        gid_list = []
        groups = self.pb.collection('groups').get_list(1, 20, {"filter": 'allowed = true'})
        for group in groups.items:
            gid_list.append(group.gid)
        return gid_list


if __name__ == "__main__":
    pb = Db()
    active = pb.add_to_team(498123938, True)
    print(active)
