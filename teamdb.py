from pocketbase import PocketBase
from dotenv import load_dotenv
import os

load_dotenv()


def on_list(tid=498123938) -> int:
    tid = tid
    pb = PocketBase(os.environ['pb'])

    p = pb.collection('team').get_list(1,20,{"filter": f'tid = {tid} && active = true'})
    return p.total_items

def in_db(tid=498123938):
    try:
        pb = PocketBase(os.environ['pb'])

        body = {
          "tid": tid,
          "active": True,
          "attended": False,

      }

        pb.collection('team').create(body)
        return True
    except Exception as e:
        print(f'In db uodate error {e}')
        return False


if __name__ == '__main__':
    # in_db()
    on_list()