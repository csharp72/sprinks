from flask import Flask, render_template, redirect, url_for, request
from sprinkler_lib import run_sprinks, shut_off_all_sprinks, get_sprinks_by_ids, get_sprink_status, SPRINKS, SPRINK_LIST
from flask_socketio import SocketIO, emit
import json
from app_secret import APP_SECRET

import logging
logging.basicConfig(filename='sprink.log', encoding='utf-8', level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = APP_SECRET
socketio = SocketIO(app)


@app.route('/')
def index():
	message = "the wonderful world of sprinks!"
	return render_template('index.html', message=message, sprinkInfo=get_sprink_status())


# @app.route('/sprinks/run/all/<int:duration>')
# def runAllSprinks(duration):
# 	sprinks = SPRINK_LIST
# 	run_sprinks(sprinks, duration * 60)
# 	message = "Running Sprinklers"
# 	return render_template('index.html', message=message, count_down=duration, sprinks=sprinks)


# @app.route('/sprinks/run/<string:sector>/<int:duration>')
# def runSprinksBySector(sector, duration):
# 	sprinks = SPRINKS[sector.lower()]
# 	run_sprinks(sprinks, duration * 60)
# 	message = "Running Sprinklers"
# 	sector = sector.capitalize()
# 	return render_template('index.html', message=message, count_down=duration, sector=sector, sprinks=sprinks)


@app.route('/sprinks/form', methods=['POST'])
def sprinkForm():
	sprink_ids = request.form.getlist('sprinks')
	duration = int(request.form.get('duration'))
	sprinks = get_sprinks_by_ids(sprink_ids)
	run_sprinks(sprinks, duration * 60)
	return redirect(url_for('index'))


# @app.route('/sprinks/run/<int:sprink_ids>/<int:duration>', methods=['POST'])
# def runSprinksById(sprink_ids, duration):
# 	sprink_ids = [int(i) for i in str(sprink_ids)]
# 	print("sprink_ids", sprink_ids)
# 	sprinks = get_sprinks_by_ids(sprink_ids)
# 	print("sprinks", sprinks)
# 	run_sprinks(sprinks, duration * 60)
# 	message = "Running Sprinklers"
# 	return render_template('index.html', message=message, count_down=duration, sprinks=sprinks)


@app.route('/sprinks/stop')
@app.route('/sprinks/off')
def sprinksStop():
	print('Stop the sprinks!!!')
	shut_off_all_sprinks()
	return redirect(url_for('index'))


@socketio.on('sprink update req')
def sprink_update():
    emit('sprink update res', json.dumps({'data': get_sprink_status()}, indent=4, sort_keys=True, default=str))


@socketio.on('connection')
def on_socket_connection():
    print('A user connected')
    emit('response', {'data': 'Welcome to the wide world of Sprinks!'})


@socketio.on('disconnect')
def on_socket_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
	# app.run(host='0.0.0.0', port=8000, debug=True)
	socketio.run(app, host='0.0.0.0', port=8000)
