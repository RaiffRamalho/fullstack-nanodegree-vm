from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

app = Flask(__name__)

@app.route('/')
def showMusicGenre():
    
    return render_template('music/musicGenre.html')

if __name__ == '__main__':
    app.secret_key = 'super_secre_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)