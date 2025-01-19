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

@app.route('/get_player_data', methods=['POST'])
def get_player_data():
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
                    player_value = random.randint(1, games[game_id]['player_count'])
                    for ip in games[game_id]['players_data']:
                        if 'value' in games[game_id]['players_data'][ip]:
                            if games[game_id]['players_data'][ip]['value'] == player_value:
                                player_value_exists = True                    
                games[game_id]['players_data'][user_ip]['value'] = player_value
                return jsonify(player_number=games[game_id]['players_data'][user_ip]['value'],game_theme=games[game_id]['game_theme'])
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
        return jsonify(players_data="Game has ended, please start a new game.")
    else:
        guessed_data = request.json.get('guessed_data')
        # Received: {'username': {'0': 'seb', '1': 'da'}, 'player_value': {'0': '445', '1': '500'}}
        # Expected: {'player_numbers': {'seb': 6, 'daph': 1}, 'guessing_status': {}, 'game_finished': False}
        # Expected: {'player_numbers': {'seb': 6, 'daph': 1}, 'guessing_status': {}, 'game_finished': False}
        for i in range(len(guessed_data['username'])):
            username = guessed_data['username'][str(i)]
            player_value = int(guessed_data['player_value'][str(i)])
            player_found = False
            for ip in games[game_id]['members_list']:
                if games[game_id]['members_list'][ip]['username'] == username:
                    player_found = True
                    user_ip = ip
            if not player_found:
                return jsonify(success=False,message="Wrong player username: " + username)
            elif games[game_id]['members_list'][user_ip]['value'] == player_value:
                games[game_id]['guessing_status'][username] = "OK"
            else:
                games[game_id]['guessing_status'][username] = "KO"
        #print(games[game_id])
        return_value = games[game_id]['guessing_status']
        #destroy_game(game_id)
        return jsonify(success=True,guessing_status=return_value)
    
@app.route('/new_game', methods=['POST'])
def new_game():
    user_ip = request.json.get('user_ip')
    username = request.json.get('username')
    #game_theme = request.json.get('game_theme')
    #player_count = request.json.get('player_count')
    #try:
    #    socket.inet_aton(user_ip)
    #except:
    #    print("Invalid IP address: " + user_ip)
    #    return jsonify(result="Invalid IP address")
    if len(games) >= 10:
        print("Too many games, please wait")
        return jsonify(success=False,message="Too many games, please wait",game_id='')
    #if not game_theme or game_theme.isspace():
    #    return jsonify(result="Game theme cannot be empty")
    #if player_count <= 0 or player_count >= 11:
    #    return jsonify(result="The game can't be played with this number of player")
    game_id = generate_random_string(8)
    if game_id in games:
        while game_id in games:
            game_id = generate_random_string(8)
    global player_numbers
    global guessing_status
    games[game_id] = {}
    games[game_id]['players_data'] = {}
    games[game_id]['members_list'] = {}
    games[game_id]['game_status'] = 'NotStarted'
    games[game_id]['members_list'][user_ip] = {'username':username,'user_type':'player'}
    games[game_id]['guessing_status'] = {}
    games[game_id]['game_theme'] = ''
    games[game_id]['player_count'] = 1
    #games[game_id]['game_master_ip'] = user_ip
    #games[game_id]['game_finished'] = False
    print("Created a new game with ID: " + game_id)
    return jsonify(success=True,message="A new game was just created",game_id=game_id)

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

@app.route('/join_game', methods=['POST'])
def join_game():
    game_id = request.json.get('game_id')
    user_ip = request.json.get('user_ip')
    username = request.json.get('username')
    if game_id in games:
        if user_ip in games[game_id]['members_list']:
            return jsonify(success=False,message="User already joined!")
        else:
            # Check if game is full
            if len(games[game_id]['members_list']) >= 11:
                return jsonify(success=False,message="This game is full!")
            # Check if username is taken
            for member_ip in games[game_id]['members_list'].keys():
                if(games[game_id]['members_list'][member_ip]['username']) == username:
                    return jsonify(success=False,message="This name is taken already, please choose another one")
            games[game_id]['members_list'][user_ip] = {'username':username,'user_type':'player'}
            return jsonify(success=True)
    else:
        return jsonify(success=False,message='Game ID not found')

@app.route('/get_members', methods=['POST'])
def get_members():
    game_id = request.json.get('game_id')
    if game_id not in games:
        return jsonify(success=False,message="Game has ended, please join a new game.")
    else:
        return_list = []
        for user_ip in games[game_id]['members_list'].keys():
            return_list.append(games[game_id]['members_list'][user_ip])
        return jsonify(sucess=True,members=return_list)

@app.route('/set_game_master', methods=['POST'])
def set_game_master():
    game_id = request.json.get('game_id')
    user_ip = request.json.get('user_ip')
    username = request.json.get('username')
    game_master_found = False
    for member_ip in games[game_id]['members_list'].keys():
        if games[game_id]['members_list'][member_ip]['user_type'] == 'game_master':
            game_master_found = True
            break
    if game_master_found:
        return jsonify(success=False,message='There is already a game master: ' + games[game_id]['game_master'])
    else:
        if user_ip not in games[game_id]['members_list'] or username == games[game_id]['members_list'][user_ip]:
            return jsonify(success=False,message='Your user was not found in this game')
        else:
            games[game_id]['members_list'][user_ip]['user_type'] = 'game_master'
            return jsonify(success=True,message='')
    
@app.route('/unset_game_master', methods=['POST'])
def unset_game_master():
    game_id = request.json.get('game_id')
    user_ip = request.json.get('user_ip')
    username = request.json.get('username')
    game_master_found = False
    success = False
    for member_ip in games[game_id]['members_list'].keys():
        if games[game_id]['members_list'][member_ip]['user_type'] == 'game_master':
            game_master_found = True
            if member_ip == user_ip and games[game_id]['members_list'][member_ip]['username'] == username:
                games[game_id]['members_list'][member_ip]['user_type'] = 'player'
                success = True
                return jsonify(success=True,message='')
    if not game_master_found:
        return jsonify(success=False,message='No game master was found for this game')
    if not success:
        return jsonify(success=True,message='You were already not a game master, the current game master is: ' + games[game_id]['game_master'])

@app.route('/start_game', methods=['POST'])
def start_game():
    game_id = request.json.get('game_id')
    #user_ip = request.json.get('user_ip') # These 2 could be use to make things safer, ignoring for the moment
    #username = request.json.get('username')
    game_theme = request.json.get('game_theme')
    player_count = request.json.get('player_count')
    if not game_theme or game_theme.isspace():
        return jsonify(success=False,message="Game theme cannot be empty")
    if player_count <= 0 or player_count >= 11:
        return jsonify(success=False,message="The game can't be played with this number of player")
    games[game_id]['game_status'] = 'Started'
    games[game_id]['game_theme'] = game_theme
    games[game_id]['player_count'] = player_count
    print("Started game: " + game_id)
    return jsonify(success=True,message="A new game just started",game_id=game_id)

@app.route('/draw_card', methods=['POST'])
def draw_card():
    game_id = request.json.get('game_id')
    username = request.json.get('username')
    user_ip = request.json.get('user_ip')
    print('Retrieving number for player: ' + username + ' with IP address: ' + user_ip)
    # Handing fringe cases
    if game_id not in games:
        return jsonify(success=False,message="Game has ended, please join a new game.")
    if user_ip not in games[game_id]['members_list'] :
        return jsonify(success=False,message="Player not found in this game.")
    # Actual normal scenario
    player_value_exists = True
    while player_value_exists:
        player_value_exists = False
        player_value = random.randint(1, games[game_id]['player_count'])
        for ip in games[game_id]['members_list']:
            if 'value' in games[game_id]['members_list'][ip]:
                if games[game_id]['members_list'][ip]['value'] == player_value:
                    player_value_exists = True                    
    games[game_id]['members_list'][user_ip]['value'] = player_value
    return jsonify(success=True,player_number=games[game_id]['members_list'][user_ip]['value'])

@app.route('/leave_game', methods=['POST'])
def leave_game():
    game_id = request.json.get('game_id')
    user_ip = request.json.get('user_ip')
    # Handing fringe cases
    if game_id not in games:
        return jsonify(success=False,message="Game doesn't exist")
    if user_ip not in games[game_id]['members_list'] :
        return jsonify(success=False,message="Player already left.")
    # Actual normal scenario
    games[game_id]['members_list'].pop(user_ip)
    # If all players left, delete game
    if len(games[game_id]['members_list']) == 0:
        games.pop(game_id)
    return jsonify(success=True)

@app.route('/get_game_theme', methods=['POST'])
def get_game_theme():
    game_id = request.json.get('game_id')
    return jsonify(success=True,game_theme=games[game_id]['game_theme'])
    

if __name__ == '__main__':
    app.run(debug=True)