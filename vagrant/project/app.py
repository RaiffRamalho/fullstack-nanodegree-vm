from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Genre, Band

app = Flask(__name__)

engine = create_engine('sqlite:///musicgenrewithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)


#JSON for all genders
@app.route('/genre/<int:genre_id>/JSON')
def genreJSON(genre_id):
    session = DBSession()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    bands = session.query(Band).filter_by(
        genre_id=genre_id).all()
    return jsonify(Bands=[band.serialize for band in bands])

#JSON for all genders

#JSON APIs to view Genre Information
@app.route('/genre/<int:genre_id>/bands/JSON')
def genreBandsJSON(genre_id):
    genre = session.query(Genre).filter_by(id = genre_id).one()
    bands = session.query(Band).filter_by(genre_id = genre_id).all()
    return jsonify(Bands=[band.serialize for band in bands])


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

#Show a genre bands
@app.route('/genre/<int:genre_id>/')
@app.route('/genre/<int:genre_id>/bands/')
def showBands(genre_id):
    session = DBSession()
    genre = session.query(Genre).filter_by(id = genre_id).one()
    # creator = getUserInfo(genre.user_id)
    bands = session.query(Band).filter_by(genre_id = genre_id).all()
    # if 'username' not in login_session or creator.id != login_session['user_id']:
    #     return render_template('publicmenu.html', bands = bands, genre = genre, creator = creator)
    # else:
    #     return render_template('menu.html', bands = bands, genre = genre, creator = creator)
    return render_template('genre/bands.html', bands = bands, genre = genre)

#Create a new band
@app.route('/genre/<int:genre_id>/bands/new/',methods=['GET','POST'])
def newBand(genre_id):
    session = DBSession()

#   if 'username' not in login_session:
#       return redirect('/login')
    genre = session.query(Genre).filter_by(id = genre_id).one()
    if request.method == 'POST':
        newBand = Band(name = request.form['name'], description = request.form['description'],
        genre_id = genre_id,user_id=genre.user_id)
        session.add(newBand)
        session.commit()
        #   flash('New Menu %s Item Successfully Created' % (newBand.name))
        return redirect(url_for('showBands', genre_id = genre_id))
    else:
        return render_template('genre/newBand.html', genre = genre)


#Edit a band
@app.route('/genre/<int:genre_id>/bands/<int:band_id>/edit', methods=['GET','POST'])
def editBand(genre_id, band_id):
    session = DBSession()
    # if 'username' not in login_session:
    #   return redirect('/login')
    editedBand = session.query(Band).filter_by(id = band_id).one()
    genre = session.query(Genre).filter_by(id = genre_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedBand.name = request.form['name']
        if request.form['description']:
            editedBand.description = request.form['description']
        session.add(editedBand)
        session.commit() 
        # flash('Menu Item Successfully Edited')
        return redirect(url_for('showBands', genre_id = genre_id))
    else:
        return render_template('genre/editBand.html', genre_id = genre_id, band = editedBand)

#Delete a band
@app.route('/genre/<int:genre_id>/bands/<int:band_id>/delete', methods = ['GET','POST'])
def deleteBand(genre_id,band_id):
    session = DBSession()
    # if 'username' not in login_session:
    #   return redirect('/login')
    genre = session.query(Genre).filter_by(id = genre_id).one()
    bandToDelete = session.query(Band).filter_by(id = band_id).one() 
    if request.method == 'POST':
        session.delete(bandToDelete)
        session.commit()
        # flash('Menu Item Successfully Deleted')
        return redirect(url_for('showBands', genre_id = genre_id))
    else:
        return render_template('genre/deleteConfirmation.html', band = bandToDelete)


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