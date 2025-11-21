import os
import pandas as pd

# In-memory store (simple). For production use Redis/db.
_store = {}

def save_uploaded_file(file_storage, sid, upload_folder):
    # Ensure folder
    os.makedirs(upload_folder, exist_ok=True)
    filename = f"{sid}_{file_storage.filename}"
    path = os.path.join(upload_folder, filename)
    file_storage.save(path)
    return path

def set_session_df(sid, df, path=None):
    _store[sid] = {
        'df': df,
        'path': path,
        'original_df': df.copy()
    }

def get_session_df(sid):
    item = _store.get(sid)
    if not item:
        return None
    return item.get('df')

def reset_session_df(sid):
    item = _store.get(sid)
    if not item:
        return
    item['df'] = item['original_df'].copy()
