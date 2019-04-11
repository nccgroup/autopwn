from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def reset_database():
    # from rest_api_demo.database.models import Post, Category  # noqa
    from autopwn2.database.models import Setting, Job, Tool, Assessment
    db.drop_all()
    db.create_all()


def with_session(fn):
    def go(*args, **kw):
        try:
            ret = fn(*args, **kw)
            db.session.commit()
            return ret
        except:
            db.session.rollback()
            raise

    return go
