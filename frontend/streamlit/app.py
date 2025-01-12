import streamlit as st
import requests
from streamlit_javascript import st_javascript
import random
import pandas as pd
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx
import os
import json
from requests.auth import HTTPBasicAuth

print('####### RUNNING INSTANCE #######')
st.set_page_config(page_title='Top Ten ADeVeP', layout='wide')
st.title('Top Ten ADeVeP')

# Setting glibal vars
global server_root_url
#server_root_url = "http://localhost:5000"
server_root_url = "https://sebril.pythonanywhere.com"
global basic_auth
basic_auth = HTTPBasicAuth(st.secrets['PY_ANYWHERE_USER'], st.secrets['PY_ANYWHERE_PW'])
global images_dict
# Check https://commons.wikimedia.org/wiki/Category:SVG_playing_cards_2
images_dict = {
    "1": ["https://upload.wikimedia.org/wikipedia/commons/3/36/Playing_card_club_A.svg","https://upload.wikimedia.org/wikipedia/commons/d/d3/Playing_card_diamond_A.svg","https://upload.wikimedia.org/wikipedia/commons/5/57/Playing_card_heart_A.svg","https://upload.wikimedia.org/wikipedia/commons/2/25/Playing_card_spade_A.svg"],
    "2": ["https://upload.wikimedia.org/wikipedia/commons/f/f5/Playing_card_club_2.svg","https://upload.wikimedia.org/wikipedia/commons/5/59/Playing_card_diamond_2.svg","https://upload.wikimedia.org/wikipedia/commons/d/d5/Playing_card_heart_2.svg","https://upload.wikimedia.org/wikipedia/commons/f/f2/Playing_card_spade_2.svg"],
    "3": ["https://upload.wikimedia.org/wikipedia/commons/6/6b/Playing_card_club_3.svg","https://upload.wikimedia.org/wikipedia/commons/8/82/Playing_card_diamond_3.svg","https://upload.wikimedia.org/wikipedia/commons/b/b6/Playing_card_heart_3.svg","https://upload.wikimedia.org/wikipedia/commons/5/52/Playing_card_spade_3.svg"],
    "4": ["https://upload.wikimedia.org/wikipedia/commons/3/3d/Playing_card_club_4.svg","https://upload.wikimedia.org/wikipedia/commons/2/20/Playing_card_diamond_4.svg","https://upload.wikimedia.org/wikipedia/commons/a/a2/Playing_card_heart_4.svg","https://upload.wikimedia.org/wikipedia/commons/2/2c/Playing_card_spade_4.svg"],
    "5": ["https://upload.wikimedia.org/wikipedia/commons/5/50/Playing_card_club_5.svg","https://upload.wikimedia.org/wikipedia/commons/f/fd/Playing_card_diamond_5.svg","https://upload.wikimedia.org/wikipedia/commons/5/52/Playing_card_heart_5.svg","https://upload.wikimedia.org/wikipedia/commons/9/94/Playing_card_spade_5.svg"],
    "6": ["https://upload.wikimedia.org/wikipedia/commons/a/a0/Playing_card_club_6.svg","https://upload.wikimedia.org/wikipedia/commons/8/80/Playing_card_diamond_6.svg","https://upload.wikimedia.org/wikipedia/commons/c/cd/Playing_card_heart_6.svg","https://upload.wikimedia.org/wikipedia/commons/d/d2/Playing_card_spade_6.svg"],
    "7": ["https://upload.wikimedia.org/wikipedia/commons/4/4b/Playing_card_club_7.svg","https://upload.wikimedia.org/wikipedia/commons/e/e6/Playing_card_diamond_7.svg","https://upload.wikimedia.org/wikipedia/commons/9/94/Playing_card_heart_7.svg","https://upload.wikimedia.org/wikipedia/commons/6/66/Playing_card_spade_7.svg"],
    "8": ["https://upload.wikimedia.org/wikipedia/commons/e/eb/Playing_card_club_8.svg","https://upload.wikimedia.org/wikipedia/commons/7/78/Playing_card_diamond_8.svg","https://upload.wikimedia.org/wikipedia/commons/5/50/Playing_card_heart_8.svg","https://upload.wikimedia.org/wikipedia/commons/2/21/Playing_card_spade_8.svg"],
    "9": ["https://upload.wikimedia.org/wikipedia/commons/2/27/Playing_card_club_9.svg","https://upload.wikimedia.org/wikipedia/commons/9/9e/Playing_card_diamond_9.svg","https://upload.wikimedia.org/wikipedia/commons/5/50/Playing_card_heart_9.svg","https://upload.wikimedia.org/wikipedia/commons/e/e0/Playing_card_spade_9.svg"],
    "10": ["https://upload.wikimedia.org/wikipedia/commons/3/3e/Playing_card_club_10.svg","https://upload.wikimedia.org/wikipedia/commons/3/34/Playing_card_diamond_10.svg","https://upload.wikimedia.org/wikipedia/commons/9/98/Playing_card_heart_10.svg","https://upload.wikimedia.org/wikipedia/commons/8/87/Playing_card_spade_10.svg"]
}

# Get the user's ip address
def get_remote_ip() -> str:
    user_ip = st_javascript("""await fetch("https://ifconfig.me/ip").then(response => response.text()) """)
    return user_ip

# Set up environment
def initialize_env():
    global curr_env
    if 'USERS_DATA' not in os.environ:
        os.environ['USERS_DATA'] = json.dumps({})
    else:
        curr_env = json.loads(os.environ['USERS_DATA'])
        if user_ip not in curr_env:
            curr_env[user_ip] = {}

# Functions assuring that the curr env var reflects what is in os.environ
def set_env_var(var_name,var_value):
    curr_env[user_ip][var_name] = var_value
    os.environ['USERS_DATA'] = json.dumps(curr_env)
def del_env_var(var_name):
    curr_env[user_ip].pop(var_name)
    os.environ['USERS_DATA'] = json.dumps(curr_env)
def in_env(var_name):
    return var_name in curr_env[user_ip]
def get_env(var_name):
    return curr_env[user_ip][var_name]

@st.fragment(run_every=1)
def get_game_players():
    print('Running fragment get_game_players')
    if in_env('GAME_ID'):
        print('Getting players')
        try:
            response = requests.post(server_root_url+"/get_players", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
            print('test')
        except:
            print('Error getting players (server not up?)')
            return
        if response.status_code != 200:
            print('Error getting players')
            return
        else:
            print('test')
            print(response.json().get('players_data'))
            if not in_env('PLAYERS_LIST'):
                print('Setting players_list for the first time')
                set_env_var('PLAYERS_LIST', json.dumps(response.json().get('players_data')))
                st.rerun()
            elif json.dumps(response.json().get('players_data')) != get_env('PLAYERS_LIST'):
                print('Updating players_list')
                set_env_var('PLAYERS_LIST', json.dumps(response.json().get('players_data')))
                st.rerun()

@st.fragment(run_every=1)
def get_game_status():
    print('Running fragment game_game_status')
    if in_env('GAME_ID'):
        print('Getting game status')
        try:
            response = requests.post(server_root_url+"/check_game_exists", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
        except:
            game_status = "Ended"
        if response.json().get('game_exists'):
            game_status = "Ongoing"
        else:
            game_status = "Ended"
        if not in_env('GAME_STATUS'):
            set_env_var('GAME_STATUS', game_status)
            st.rerun()
        if get_env('GAME_STATUS') != game_status:
            set_env_var('GAME_STATUS', game_status)
            st.rerun()
        
def reset_session(caller,refresh=True):
    print("Reset cache initiated by " + caller)
    if caller == "game_master":
        try:
            response = requests.post(server_root_url+"/destroy_game", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
        except:
            st.write("Error destroying game. Is the server up?")
    if in_env('GAME_ID'):
        del_env_var('GAME_ID')
    if in_env('USER_TYPE'):
        del_env_var('USER_TYPE')
    if in_env('PLAYER_NUMBER'):
        del_env_var('PLAYER_NUMBER')
    if in_env('PLAYER_ID'):
        del_env_var('PLAYER_ID')
    if in_env('PLAYERS_LIST'):
        del_env_var('PLAYERS_LIST')
    if in_env('GAME_STATUS'):
        del_env_var('GAME_STATUS')
    if refresh:
        st.rerun()

def player_ui():
    st.title("You are a Player 🃏")
    if not in_env('GAME_ID'):
        game_id = st.text_input("Game ID")
        if st.button("Join game"):
            try:
                response = requests.post(server_root_url+"/check_game_exists", json={"game_id": game_id}, auth=basic_auth)
            except:
                st.write("Error joining game. Is the server up?")
                return
            if response.json().get('game_exists'):
                set_env_var('GAME_ID', game_id)
                st.rerun()
            else:
                st.write("Game does not exist!")
    else:
        get_game_status()
        if in_env('GAME_STATUS'):
            if get_env('GAME_STATUS') == "Ended":
                st.write("Game has ended, please join a new game.")
            else:
                if not in_env('PLAYER_NUMBER'):
                    player_id = st.text_input("Player ID")
                    if st.button("Get number"):
                        try:
                            response = requests.post(server_root_url+"/get_number", json={"game_id": get_env('GAME_ID'), "player_id": player_id, "user_ip": user_ip}, auth=basic_auth)
                            print(response.json())
                        except:
                            st.write("Error getting number. Is the server up?")
                            return
                        if response.json().get('player_number') == "Player ID already exists!.":
                            st.write("Player ID already exists!")
                        elif str(response.json().get('player_number')).startswith("You are already connected"):
                            st.write(response.json().get('player_number'))
                        else:
                            set_env_var('PLAYER_ID', player_id)
                            set_env_var('PLAYER_NUMBER', str(response.json().get('player_number')))
                            st.rerun()
                else:
                    st.title(get_env('PLAYER_ID') + ", your card is: " + get_env('PLAYER_NUMBER'))
                    image_url = random.choice(images_dict[get_env('PLAYER_NUMBER')])
                    st.image(image_url,caption=get_env('PLAYER_NUMBER'))

def game_master_ui():
    st.title("You are the Game Master 🧙‍♂️")
    if not in_env('GAME_ID'):
        if st.button("Start new game"):
            try:
                response = requests.post(server_root_url+"/new_game", json={"user_ip": user_ip}, auth=basic_auth)
            except:
                st.write("Error starting new game. Is the server up?")
                return
            if response.json().get('result') == "Too many games, please wait":
                st.write("Too many games, please wait")
            elif response.json().get('result') == "Invalid IP address":
                st.write("Invalid IP address")
            else:
                st.write(response.json().get('result'))
                set_env_var('GAME_ID', response.json().get('result').split("ID: ")[1])
                st.rerun()
    else:
        st.write("Game ID: " + get_env('GAME_ID'))
        st.header("Vote for the players values")
        get_game_players() # run a loop to check for potential player changes
        if in_env('PLAYERS_LIST'):
            players_list = json.loads(get_env('PLAYERS_LIST'))
            print(players_list)
            if len(players_list)== 0:
                st.write("Waiting for players to join the game...")
            else:
                list_for_df = []
                for player in players_list:
                    dict_for_df = {}
                    dict_for_df['player_id'] = player
                    dict_for_df['player_value'] = ''
                    list_for_df += [dict_for_df]
                df = pd.DataFrame(list_for_df)
                modified_df = st.data_editor(
                    df,
                    column_config={
                        "player_id": st.column_config.Column(
                            "Player Name",
                            help='The name of the player',
                            disabled=True
                            ),
                        "player_value": st.column_config.NumberColumn(
                            "Value",
                            help='The value you think this player has',
                            min_value=1,
                            max_value=10,
                            step=1,
                            required=True,
                            disabled=False,
                            default=0,
                            )
                    },
                    hide_index=True
                )
                if st.button("Submit"):
                    print(modified_df.to_dict())
                    try:
                        response = requests.post(server_root_url+"/guess_all_players", json={"game_id": get_env('GAME_ID'), "guessed_data": modified_df.to_dict()}, auth=basic_auth)
                    except:
                        st.write("Error submitting votes. Is the server up?")
                        return
                    guessing_status = response.json().get('guessing_status')
                    if all(status == 'OK' for status in guessing_status.values()):
                        st.balloons()
                        st.write("Congratulations! All values are correct. The game will now end, please start a new one.")
                        reset_session("game_master",refresh=False)
                    else:
                        st.write("Unfortunately you made at least one mistake, see results below:")
                        st.write(response.json().get('guessing_status'))
                        st.write("The game will now end, please start a new one.")
                        reset_session("game_master",refresh=False)

def spectator_ui():
    st.title("You are a Spectator 👀")
    if st.button("Get games"):
            try:
                response = requests.post(server_root_url+"/get_games", auth=basic_auth)
            except:
                st.write("Error getting games. Is the server up?")
                return
            st.write(response.json().get('games_data'))
    if not in_env('GAME_ID'):
        game_id = st.text_input("Game ID")
        if st.button("Spectate game"):
            try:
                response = requests.post(server_root_url+"/check_game_exists", json={"game_id": game_id}, auth=basic_auth)
            except:
                st.write("Error checking game. Is the server up?")
                return
            if response.json().get('game_exists'):
                set_env_var('GAME_ID', game_id)
                st.rerun()
            else:
                st.write("Game does not exist!")
    else:
        if st.button("Get all numbers"):
            try:
                response = requests.post(server_root_url+"/all_numbers", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
            except:
                st.write("Error getting all numbers. Is the server up?")
                return
            st.write(response.json().get('player_numbers'))
        if st.button("Get players"):
            try:
                response = requests.post(server_root_url+"/get_players", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
            except:
                st.write("Error getting players data. Is the server up?")
                return
            st.write(response.json().get('players_data'))
        if st.button("Get guessing status"):
            try:
                response = requests.post(server_root_url+"/debug_get_guessing_status", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
            except:
                st.write("Error getting guessing status. Is the server up?")
                return
            st.write(response.json().get('guessing_status'))

#def refresh():
#    js_script = "reload()"
#    st_javascript(js_script)

########################### MAIN ###########################
# Get current user's ip and initialize environment
global user_ip
user_ip = get_remote_ip()
initialize_env()
print(curr_env)
#print('User IP: ' + user_ip)
#st.write('User IP: ' + user_ip)

if not in_env('USER_TYPE'):
    # Define user type
    option = st.selectbox(
        "User type",
        ("Player", "Game Master", "Spectator"),
        index=None,
        placeholder="Pick your user type",
    )

    if option == "Player":
        set_env_var('USER_TYPE', "player")
        st.rerun()
    elif option == "Game Master":
        set_env_var('USER_TYPE', "game_master")
        st.rerun()
    elif option == "Spectator":
        set_env_var('USER_TYPE', "spectator")
        st.rerun()
else:
    if get_env('USER_TYPE') == "player":
        if st.button("Back"):
            reset_session("player")
        player_ui()
    elif get_env('USER_TYPE') == "game_master":
        if st.button("Back"):
            reset_session("game_master")
        game_master_ui()
    elif get_env('USER_TYPE') == "spectator":
        if st.button("Back"):
            reset_session("spectator")
        spectator_ui()
    else:
        st.write("Invalid user type, please refresh and reset your cache (Ctrl+F5)")
