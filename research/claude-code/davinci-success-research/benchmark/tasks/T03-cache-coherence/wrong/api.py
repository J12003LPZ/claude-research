def rename_user(cached, user_id, new_name):
    user = dict(cached.get(user_id))
    user["name"] = new_name
    cached.store.write(user_id, user)
    cached._cache.clear()
    return user


def delete_user(cached, user_id):
    cached.store.remove(user_id)
    cached._cache.clear()
