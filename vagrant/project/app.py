from flask import Flask, render_template, request
from flask import redirect, url_for, jsonify, flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Genre, Band, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)

engine = create_engine('sqlite:///musicgenrewithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Project Music Genre Application"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print 'Tokens client ID does not match apps.'
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'),
            200
            )
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        print(user_id)
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width:300px; height:300px;border-radius:150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    print "done!"
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    oauth2uri = 'https://accounts.google.com/o/oauth2/revoke?token=%s'
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps(
            'Current user not connected.'),
            401
            )
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = oauth2uri % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps('Successfully disconnected.'),
            200
            )
        response.headers['Content-Type'] = 'application/json'
        session = DBSession()
        genres = session.query(Genre).all()
        return render_template('music/publicgenres.html', genres=genres)
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# User Helper Functions

def createUser(login_session):
    session = DBSession()
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    session = DBSession()
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    session = DBSession()
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# JSON for all genders
@app.route('/genre/<int:genre_id>/JSON')
def genreJSON(genre_id):
    session = DBSession()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    bands = session.query(Band).filter_by(
        genre_id=genre_id).all()
    return jsonify(Bands=[band.serialize for band in bands])


# JSON APIs to view Genre Information
@app.route('/genre/<int:genre_id>/bands/JSON')
def genreBandsJSON(genre_id):
    session = DBSession()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    bands = session.query(Band).filter_by(genre_id=genre_id).all()
    return jsonify(Bands=[band.serialize for band in bands])


# home route show all bands
@app.route('/')
@app.route('/genre')
def showGenre():
    session = DBSession()
    genres = session.query(Genre).all()
    if 'username' not in login_session:
        return render_template('music/publicgenres.html', genres=genres)
    else:
        return render_template('music/genres.html', genres=genres)


# route to get bands of a genre
@app.route('/genre/<int:genre_id>/')
def genreBands(genre_id):
    session = DBSession()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    bands = session.query(Band).filter_by(genre_id=genre.id)
    return render_template('genre/bands.html', genre=genre, bands=bands)


@app.route('/genre/new/', methods=['GET', 'POST'])
def newGenre():
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newGenre = Genre(
            name=request.form['name'],
            user_id=login_session['user_id']
            )
        session.add(newGenre)
        session.commit()
        return redirect(url_for('showGenre'))
    else:
        return render_template('music/newGenre.html')


@app.route('/genre/<int:genre_id>/edit/', methods=['GET', 'POST'])
def editGenre(genre_id):
    session = DBSession()
    editedGenre = session.query(Genre).filter_by(id=genre_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedGenre.user_id != login_session['user_id']:
        returnurl = ""
        returnurl += "<script>function myFunction() {alert('You are not "
        returnurl += "authorized to edit this genre."
        returnurl += " Please create your own genre in order to edit.')"
        returnurl += ";}</script><body onload='myFunction()''>"
        return returnurl
    if request.method == 'POST':
        if request.form['name']:
            editedGenre.name = request.form['name']
        session.add(editedGenre)
        session.commit()
        return redirect(url_for('showGenre'))
    else:
        return render_template('music/editGenre.html', genre=editedGenre)


@app.route('/genre/<int:genre_id>/delete/', methods=['GET', 'POST'])
def deleteGenre(genre_id):
    session = DBSession()
    genreToDelete = session.query(Genre).filter_by(id=genre_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if genreToDelete.user_id != login_session['user_id']:
        returnurl = ""
        returnurl += "<script>function myFunction() {alert('You are not "
        returnurl += "authorized to delete this genre. Please"
        returnurl += "create your own genre in order to delete.');"
        returnurl += "}</script><body onload='myFunction()''>"
        return returnurl
    if request.method == 'POST':
        session.delete(genreToDelete)
        session.commit()
        return redirect(url_for('showGenre'))
    else:
        return render_template(
                                'music/deleteconfirmation.html',
                                genre=genreToDelete
                                )


# Show a genre bands
@app.route('/genre/<int:genre_id>/')
@app.route('/genre/<int:genre_id>/bands/')
def showBands(genre_id):
    session = DBSession()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    creator = getUserInfo(genre.user_id)
    bands = session.query(Band).filter_by(genre_id=genre_id).all()
    logsess_user = login_session['user_id']
    if 'username' not in login_session or creator.id != logsess_user:
        return render_template(
                                'genre/publicbands.html',
                                bands=bands,
                                genre=genre,
                                creator=creator)
    else:
        return render_template(
                                'genre/bands.html',
                                bands=bands,
                                genre=genre,
                                creator=creator)


# Create a new band
@app.route('/genre/<int:genre_id>/bands/new/', methods=['GET', 'POST'])
def newBand(genre_id):
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    genre = session.query(Genre).filter_by(id=genre_id).one()
    if login_session['user_id'] != genre.user_id:
        returnurl = ""
        returnurl += "<script>function myFunction() {alert('You are not "
        returnurl += "authorized to add bands to this genre. Please"
        returnurl += "create your own genre in order to add bands.');"
        returnurl += " }</script><body onload='myFunction()''>"
        return returnurl
    if request.method == 'POST':
        newBand = Band(
                        name=request.form['name'],
                        description=request.form['description'],
                        genre_id=genre_id,
                        user_id=genre.user_id
                        )
        session.add(newBand)
        session.commit()
        return redirect(url_for('showBands', genre_id=genre_id))
    else:
        return render_template('genre/newBand.html', genre=genre)


# Edit a band
@app.route(
        '/genre/<int:genre_id>/bands/<int:band_id>/edit',
        methods=['GET', 'POST']
        )
def editBand(genre_id, band_id):
    session = DBSession()
    if 'username' not in login_session:
        return redirect('/login')
    editedBand = session.query(Band).filter_by(id=band_id).one()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    if login_session['user_id'] != genre.user_id:
        returnurl = ""
        returnurl += "<script>function myFunction() {alert('You are not "
        returnurl += "authorized to edit bands to this genre. Please"
        returnurl += "create your own genre in order to edit bands.');"
        returnurl += "}</script><body onload='myFunction()''>"
        return returnurl
    if request.method == 'POST':
        if request.form['name']:
            editedBand.name = request.form['name']
        if request.form['description']:
            editedBand.description = request.form['description']
        session.add(editedBand)
        session.commit()
        return redirect(url_for('showBands', genre_id=genre_id))
    else:
        return render_template(
                                'genre/editBand.html',
                                genre_id=genre_id,
                                band=editedBand
                                )


# Delete a band
@app.route(
        '/genre/<int:genre_id>/bands/<int:band_id>/delete',
        methods=['GET', 'POST']
        )
def deleteBand(genre_id, band_id):
    session = DBSession()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    bandToDelete = session.query(Band).filter_by(id=band_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['user_id'] != genre.user_id:
        returnurl = ""
        returnurl += "<script>function myFunction() {alert('You are not "
        returnurl += "authorized to edit bands to this genre. Please "
        returnurl += "create your own genre in order to edit bands.');"
        returnurl += "}</script><body onload='myFunction()''>"
        return returnurl
    if request.method == 'POST':
        session.delete(bandToDelete)
        session.commit()
        return redirect(url_for('showBands', genre_id=genre_id))
    else:
        return render_template(
                                'genre/deleteConfirmation.html',
                                band=bandToDelete)


# route to shutdown the server
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
