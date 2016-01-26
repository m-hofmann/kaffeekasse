import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

logger = logging.getLogger(__name__)


engine = create_engine("sqlite:////tmp/example.db", convert_unicode=True)
Base = declarative_base()

from kaffeekasse.model import *
Base.metadata.bind = engine
Base.metadata.create_all()

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def create_debug_database():
    from kaffeekasse.model import User, IdentificationToken
    db_session = Session()
    if db_session.query(User).count() == 0:
        logger.info("creating test users")

        werner_webservice = User("Werner Webservice", 1337)
        werner_token = IdentificationToken(3681409604)
        werner_webservice.identification_tokens.append(werner_token)
        db_session.add(werner_webservice)

        thorsten_tester = User("Thorsten Tester", 4711)
        thorsten_token = IdentificationToken(2223049027)
        thorsten_tester.identification_tokens.append(thorsten_token)
        db_session.add(thorsten_tester)
    db_session.commit()
    Session.remove()

