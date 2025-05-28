from .core import get_db
from .models import User, File


def add_user(tg_user):
    db = next(get_db())
    user = db.query(User).filter_by(tg_id=tg_user.id).first()
    if not user:
        user = User(
            tg_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name
        )
        db.add(user)
        db.commit()


def save_file(tg_id, filename, content):
    db = next(get_db())
    user = db.query(User).filter_by(tg_id=tg_id).first()
    new_file = File(filename=filename, content=content, user=user)
    db.add(new_file)
    db.commit()
    return new_file.id


# Получение файла по ID
def get_file(file_id):
    db = next(get_db())
    return db.query(File).filter_by(id=file_id).first()


def delete_file(file_id: int):
    db = next(get_db())
    file = db.query(File).filter(File.id == file_id).first()
    if file:
        db.delete(file)
        db.commit()
        return True
    return False


# Получение всех файлов
def get_files(tg_id):
    db = next(get_db())
    user = db.query(User).filter_by(tg_id=tg_id).first()
    if user:
        return db.query(File).filter_by(user_id=user.id).all()
