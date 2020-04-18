from pymongo import MongoClient
from settings import MONGO_DB, MONGODB_LINK

mdb = MongoClient(MONGODB_LINK)[MONGO_DB]


def search_or_save_user(mdb, effective_user, message):
    user = mdb.users.find_one({"user_id": effective_user.id})
    if not user:
        user = {
            "user_id": effective_user.id,
            "first_name": effective_user.first_name,
            "last_name": effective_user.last_name,
            "chat_id": message.chat.id
        }
        mdb.users.insert_one(user)
    return user

def search_user_task(mdb, user, user_data):
    mdb.user.update_one(
        {'id': user['_id']},
        {'$set': {'task': {'task_title': user_data['task_title'],
                           'deadline_date': user_data['deadline_date'],
                           'notification_date': user_data['notification_date']}
                  }
        }
    )
    return user
