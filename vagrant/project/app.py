from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Genre, Band

app = Flask(__name__)

engine = create_engine('sqlite:///musicgenrewithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


#home route
@app.route('/')
@app.route('/genre')
def showGenre():
    genres = session.query(Genre).all()
    output = ''
    for genre in genres:
        output += genre.name
        output += '</br>'
    return output
    # return render_template('music/genres.html')


#route to get bands of a genre
@app.route('/genre/<int:genre_id>/')
def genreBands(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    bands = session.query(Band).filter_by(genre_id=genre.id)
    output = ''
    for b in bands:
        output += '</br>'
        output += b.name
        output += '</br>'
        output += b.description
        output += '</br>'
    return output




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