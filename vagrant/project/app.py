from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Genre, Band

app = Flask(__name__)

engine = create_engine('sqlite:///musicgenrewithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)



#home route show all bands
@app.route('/')
@app.route('/genre')
def showGenre():
    session = DBSession()
    genres = session.query(Genre).all()
    return render_template('music/genres.html', genres=genres)


#route to get bands of a genre
@app.route('/genre/<int:genre_id>/')
def genreBands(genre_id):
    session = DBSession()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    bands = session.query(Band).filter_by(genre_id=genre.id)
    return render_template('genre/bands.html',genre=genre, bands=bands)

@app.route('/genre/new/', methods=['GET', 'POST'])
def newGenre():
    session = DBSession()
    if request.method == 'POST':
        newGenre = Genre(name=request.form['name'], user_id=1)
        session.add(newGenre)
        session.commit()
        return redirect(url_for('showGenre'))
    else:
        return render_template('music/newGenre.html')


@app.route('/genre/<int:genre_id>/edit/', methods=['GET', 'POST'])
def editGenre(genre_id ):
    session = DBSession()
    editedGenre = session.query(Genre).filter_by(id = genre_id).one()

    if request.method == 'POST':
        if request.form['name']:
            editedGenre.name = request.form['name']
        session.add(editedGenre)
        session.commit() 
        return redirect(url_for('showGenre'))
    else:
        return render_template('music/editGenre.html', genre = editedGenre)


@app.route('/genre/<int:genre_id>/delete/', methods=['GET', 'POST'])
def deleteGenre(genre_id):
    session = DBSession()
    genreToDelete = session.query(Genre).filter_by(id=genre_id).one()
    if request.method == 'POST':
        session.delete(genreToDelete)
        session.commit()
        return redirect(url_for('showGenre'))
    else:
        return render_template('music/deleteconfirmation.html', genre=genreToDelete)

# @app.route('/genre/<int:genre_id>/new/', methods=['GET', 'POST'])
# def newMenuItem(genre_id):
#     if request.method == 'POST':
#         genre = session.query(Genre).filter_by(id=genre_id).one()
#         newBand = Band(name=request.form['name'], description=request.form['description'], genre_id=genre_id)
#         session.add(newBand)
#         session.commit()
#         return redirect(url_for('genre/bands.html', genre=genre))
#     else:
#         return render_template('newmenuitem.html', genre=genre)



#route to shutdown the server
@app.route('/shutdown')
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

if __name__ == '__main__':
    app.secret_key = 'super_secre_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)