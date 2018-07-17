from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Genre, Base, Band, User

engine = create_engine('sqlite:///musicgenrewithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twx400.png')
session.add(User1)
session.commit()

# bands for pop
genre1 = Genre(user_id=1, name="Pop")

session.add(genre1)
session.commit()

band1 = Band(
  user_id=1,
  name="Michael Jackson",
  description="king of pop",
  genre=genre1
  )

session.add(band1)
session.commit()


band2 = Band(
  user_id=1,
  name="Nsycn",
  description="famous boy band",
  genre=genre1
  )

session.add(band2)
session.commit()

# bands for rock
genre2 = Genre(user_id=1, name="Rock")

session.add(genre2)
session.commit()

band3 = Band(
  user_id=1,
  name="The strokes",
  description="Natural rock",
  genre=genre2
  )

session.add(band3)
session.commit()


band4 = Band(
  user_id=1,
  name="Beatles",
  description="King of rock",
  genre=genre2
  )

session.add(band4)
session.commit()


print "added bands!"
