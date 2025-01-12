from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import random
import string
import socket

# TODO: handle only game player can make a game end etc (hardening)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Store game object
games = {}

def generate_random_string(length):
    letters_and_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

@app.route('/')
def home():
    return jsonify(message="Welcome to the Backend API!")

@app.route('/get_number', methods=['POST'])
def get_number():
    game_id = request.json.get('game_id')
    player_id = request.json.get('player_id')
    user_ip = request.json.get('user_ip')
    print('Retrieving number for player: ' + player_id + ' with IP address: ' + user_ip)
    # If the game doesn't exist anymore
    if game_id not in games:
        return jsonify(player_number="Game has ended, please join a new game.")
    # If the user has never joined the game before
    if user_ip not in games[game_id]['players_data'] :
        # Ensure game hasn't reached the maximum number of players & the player id is not taken
        if len(games[game_id]['players_data']) < 10:
            player_exists = False
            for ip in games[game_id]['players_data']:
                if player_id == games[game_id]['players_data'][ip]['player_id']:
                    player_exists = True
            if player_exists:
                return jsonify(player_number="Player ID already exists!")
            # Add the player to the game, ensuring their number is unique
            else:
                games[game_id]['players_data'][user_ip] = {}
                games[game_id]['players_data'][user_ip]['player_id'] = player_id
                player_value_exists = True
                while player_value_exists:
                    player_value_exists = False
                    player_value = random.randint(1, 10)
                    for ip in games[game_id]['players_data']:
                        if games[game_id]['players_data'][ip]['value'] == player_value:
                            player_value_exists = True                    
                games[game_id]['players_data'][user_ip]['value'] = player_value
                return jsonify(player_number=games[game_id]['players_data'][user_ip]['value'])
        else:       
            return jsonify(player_number="Game is full!")
    # If the user has already joined the game before, retrieve their associated value (unless they provided a different user id, then throw an error)
    else:
        if player_id == games[game_id]['players_data'][user_ip]['player_id']:
            return jsonify(player_number=games[game_id]['players_data'][user_ip]['value'])
        else:
            return jsonify(player_number="You are already connected with the ID: '"+ games[game_id]['players_data'][user_ip]['player_id'] + "'. Please use it to reconnect.")

@app.route('/all_numbers', methods=['POST'])
def all_numbers():
    game_id = request.json.get('game_id')
    return jsonify(player_numbers=games[game_id]['players_data'])

@app.route('/check_game_exists', methods=['POST'])
def check_game_exists():
    game_id = request.json.get('game_id')
    if game_id in games:
        return jsonify(game_exists=True)
    else:
        return jsonify(game_exists=False)
    
@app.route('/destroy_game', methods=['POST'])
def destroy_game(game_id=''):
    if game_id == '':
        game_id = request.json.get('game_id')
    if game_id not in games:
        abort(404)
    games.pop(game_id)

@app.route('/guess_one_player', methods=['POST'])
def guess_one_player():
    game_id = request.json.get('game_id')
    #if games[game_id]['game_finished']:
    if 'game_id' not in games:
        return jsonify(result="Game is finished, please start a new one")
    player_id = request.json.get('player_id')
    player_value = request.json.get('player_value')
    player_found = False
    for ip in games[game_id]['players_data']:
        if games[game_id]['players_data'][ip]['player_id'] == player_id:
            player_found = True
            user_ip = ip
    if not player_found:
        return jsonify(result="Wrong player ID")
    elif games[game_id]['players_data'][user_ip]['value'] == player_value:
        games[game_id]['guessing_status'][player_id] = "OK"
        result_msg = "Correct!"
        if len(games[game_id]['players_data'].keys()) == len(games[game_id]['guessing_status'].keys()):
            if all(value == "OK" for value in games[game_id]['guessing_status'].values()):
                result_msg += "All players guessed correctly! The game will end."
            destroy_game(game_id)
        return jsonify(result=result_msg)
    else:
        games[game_id]['guessing_status'][player_id] = "KO"
        return jsonify(result="Incorrect!")
    
@app.route('/guess_all_players', methods=['POST'])
def guess_all_players():
    game_id = request.json.get('game_id')
    if game_id not in games:
        return jsonify(players_data="Game has ended, please join a new game.")
    else:
        #if games[game_id]['game_finished']:
        #return jsonify(result="Game is finished, please start a new one")
        guessed_data = request.json.get('guessed_data')

        print(guessed_data)
        # Received: {'player_id': {'0': 'seb', '1': 'da'}, 'player_value': {'0': '445', '1': '500'}}
        # Expected: {'player_numbers': {'seb': 6, 'daph': 1}, 'guessing_status': {}, 'game_finished': False}
        for i in range(len(guessed_data['player_id'])):
            player_id = guessed_data['player_id'][str(i)]
            player_value = int(guessed_data['player_value'][str(i)])
            player_found = False
            for ip in games[game_id]['players_data']:
                if games[game_id]['players_data'][ip]['player_id'] == player_id:
                    player_found = True
                    user_ip = ip
            if not player_found:
                return jsonify(result="Wrong player ID")
            elif games[game_id]['players_data'][user_ip]['value'] == player_value:
                games[game_id]['guessing_status'][player_id] = "OK"
            else:
                games[game_id]['guessing_status'][player_id] = "KO"
        print(games[game_id])
        return_value = games[game_id]['guessing_status']
        destroy_game(game_id)
        return jsonify(guessing_status=return_value)
    
@app.route('/new_game', methods=['POST'])
def new_game():
    user_ip = request.json.get('user_ip')
    try:
        socket.inet_aton(user_ip)
    except:
        print("Invalid IP address: " + user_ip)
        return jsonify(result="Invalid IP address")
    if len(games) >= 10:
        print("Too many games, please wait")
        return jsonify(result="Too many games, please wait")
    game_id = generate_random_string(8)
    if game_id in games:
        while game_id in games:
            game_id = generate_random_string(8)
    global player_numbers
    global guessing_status
    games[game_id] = {}
    games[game_id]['players_data'] = {}
    games[game_id]['guessing_status'] = {}
    games[game_id]['game_master_ip'] = user_ip
    #games[game_id]['game_finished'] = False
    print("Created a new game with ID: " + game_id)
    return jsonify(result="A new game just started! ID: " + game_id)

@app.route('/debug_get_guessing_status', methods=['POST'])
def debug_get_guessing_status():
    game_id = request.json.get('game_id')
    if game_id not in games:
        return jsonify(players_data="Game has ended, please join a new game.")
    else:
        return jsonify(guessing_status=games[game_id]['guessing_status'])

@app.route('/get_players', methods=['POST'])
def get_players():
    game_id = request.json.get('game_id')
    if game_id not in games:
        abort(404)
        #return jsonify(players_data="Game has ended, please join a new game.")
    else:
        return_list = []
        for user_ip in games[game_id]['players_data']:
            return_list.append(games[game_id]['players_data'][user_ip]['player_id'])
        return jsonify(players_data=return_list)

@app.route('/get_games', methods=['POST'])
def get_games():
    return jsonify(games_data=games)

if __name__ == '__main__':
    app.run(debug=True)