from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from kaffeekasse.database import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    balance_as_eur_cents = Column(Integer)

    identification_tokens = relationship("IdentificationToken", back_populates="user")

    def __init__(self, name, balance_as_eur_cents):
        self.name = name
        self.balance_as_eur_cents = balance_as_eur_cents

    def __repr__(self):
        return "<User {0}>".format(self.name)


class IdentificationToken(Base):
    __tablename__ = 'identification'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))

    user = relationship("User", back_populates="identification_tokens")

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return "<IdentificationToken {0}>".format(self.id)
