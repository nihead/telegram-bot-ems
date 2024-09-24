from pocketbase import PocketBase
from dotenv import load_dotenv
import os

load_dotenv()

class Db():
    def __init__(self):
        self.pb = PocketBase(os.environ['pb'])

    def on_list(self, tid):
        p = self.pb.collection('team').get_list(1, 20, {"filter": f'tid = {tid} && active = true'})
        return p.total_items

    def add_to_team(self, tid):
        try:
            body = {
                "tid": tid,
                "active": True,
                "attended": False,

            }

            self.pb.collection('team').create(body)
            return True
        except Exception as e:
            print(f'In db uodate error {e}')
            return False
