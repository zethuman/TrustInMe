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


def search_or_save_task(mdb, effective_user, user_data):
    task = {
        "user_id": effective_user.id,
        'task_title': user_data['task_title'],
        'deadline_date': user_data['deadline_date'],
        'notification_date': user_data['notification_date'],
        'task_status': user_data['task_status']
    }
    mdb.tasks.insert_one(task)
    return task


