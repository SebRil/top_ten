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

global server_root_url
#server_root_url = "http://localhost:5000"
server_root_url = "https://sebril.pythonanywhere.com"
global basic_auth
basic_auth = HTTPBasicAuth(st.secrets['PY_ANYWHERE_USER'], st.secrets['PY_ANYWHERE_PW'])
global images_dict
# Check https://commons.wikimedia.org/wiki/Category:SVG_playing_cards_2
images_dict = {
    "1": ["https://upload.wikimedia.org/wikipedia/commons/3/36/Playing_card_club_A.svg","https://upload.wikimedia.org/wikipedia/commons/d/d3/Playing_card_diamond_A.svg"],
    "2": ["https://upload.wikimedia.org/wikipedia/commons/f/f5/Playing_card_club_2.svg","https://upload.wikimedia.org/wikipedia/commons/5/59/Playing_card_diamond_2.svg"],
    "3": ["https://upload.wikimedia.org/wikipedia/commons/6/6b/Playing_card_club_3.svg","https://upload.wikimedia.org/wikipedia/commons/8/82/Playing_card_diamond_3.svg"],
    "4": ["https://upload.wikimedia.org/wikipedia/commons/3/3d/Playing_card_club_4.svg","https://upload.wikimedia.org/wikipedia/commons/2/20/Playing_card_diamond_4.svg"],
    "5": ["https://upload.wikimedia.org/wikipedia/commons/5/50/Playing_card_club_5.svg","https://upload.wikimedia.org/wikipedia/commons/f/fd/Playing_card_diamond_5.svg"],
    "6": ["https://upload.wikimedia.org/wikipedia/commons/a/a0/Playing_card_club_6.svg","https://upload.wikimedia.org/wikipedia/commons/8/80/Playing_card_diamond_6.svg"],
    "7": ["https://upload.wikimedia.org/wikipedia/commons/4/4b/Playing_card_club_7.svg","https://upload.wikimedia.org/wikipedia/commons/e/e6/Playing_card_diamond_7.svg"],
    "8": ["https://upload.wikimedia.org/wikipedia/commons/e/eb/Playing_card_club_8.svg","https://upload.wikimedia.org/wikipedia/commons/7/78/Playing_card_diamond_8.svg"],
    "9": ["https://upload.wikimedia.org/wikipedia/commons/2/27/Playing_card_club_9.svg","https://upload.wikimedia.org/wikipedia/commons/9/9e/Playing_card_diamond_9.svg"],
    "10": ["https://upload.wikimedia.org/wikipedia/commons/3/3e/Playing_card_club_10.svg","https://upload.wikimedia.org/wikipedia/commons/3/34/Playing_card_diamond_10.svg"]
}

def get_remote_ip() -> str:
    """Get remote ip."""
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None
        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return None
    except Exception as e:
        return None
    return session_info.request.remote_ip

print('####### RUNNING INSTANCE #######')
print('Session state:')
#print(st.session_state)
#print(os.environ)

st.set_page_config(page_title='Top Ten ADeVeP', layout='wide')
st.title('Top Ten ADeVeP')

global user_ip
user_ip = get_remote_ip()
# DEBUG
if 'USER_IP' in os.environ:
    user_ip = os.environ['USER_IP']
else:
    if user_ip == "::1":
        user_ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
    os.environ['USER_IP'] = user_ip

st.write('User IP: ' + user_ip)
print('User IP: ' + user_ip)

@st.fragment(run_every=1)
def get_game_players():
    print('Running fragment get_game_players')
    if 'GAME_ID' in os.environ:
        print('Getting players')
        try:
            response = requests.post(server_root_url+"/get_players", json={"game_id": os.environ['GAME_ID']}, auth=basic_auth)
        except:
            print('Error getting players (server not up?)')
            return
        if response.status_code != 200:
            print('Error getting players')
            return
        else:
            print(response.json().get('players_data'))
            if 'PLAYERS_LIST' not in os.environ:
                print('Setting players_list for the first time')
                os.environ['PLAYERS_LIST'] = json.dumps(response.json().get('players_data'))
                st.rerun()
            elif json.dumps(response.json().get('players_data')) != os.environ['PLAYERS_LIST']:
                print('Updating players_list')
                os.environ['PLAYERS_LIST'] = json.dumps(response.json().get('players_data'))
                st.rerun()

@st.fragment(run_every=1)
def get_game_status():
    print('Running fragment game_game_status')
    if 'GAME_ID' in os.environ:
        print('Getting game status')
        try:
            response = requests.post(server_root_url+"/check_game_exists", json={"game_id": os.environ['GAME_ID']}, auth=basic_auth)
        except:
            game_status = "Ended"
        if response.json().get('game_exists'):
            game_status = "Ongoing"
        else:
            game_status = "Ended"
        if 'GAME_STATUS' not in os.environ:
            os.environ['GAME_STATUS'] = game_status
            st.rerun()
        if os.environ['GAME_STATUS'] != game_status:
            os.environ['GAME_STATUS'] = game_status
            st.rerun()
        
def reset_session(caller,refresh=True):
    print("Reset cache initiated by " + caller)
    if caller == "game_master":
        try:
            response = requests.post(server_root_url+"/destroy_game", json={"game_id": os.environ['GAME_ID']}, auth=basic_auth)
        except:
            st.write("Error destroying game. Is the server up?")
    if 'GAME_ID' in os.environ:
        del os.environ['GAME_ID']
    if 'USER_TYPE' in os.environ:
        del os.environ['USER_TYPE']
    if 'PLAYER_NUMBER' in os.environ:
        del os.environ['PLAYER_NUMBER']
    if 'PLAYER_ID' in os.environ:
        del os.environ['PLAYER_ID']
    if 'PLAYERS_LIST' in os.environ:
        del os.environ['PLAYERS_LIST']
    if 'GAME_STATUS' in os.environ:
        del os.environ['GAME_STATUS']
    #st.session_state.pop('game_id', None)
    #st.session_state.pop('user_type', None)
    #st.session_state.pop('player_number', None)
    #st.session_state.pop('players_list', None)
    #st.session_state.pop('player_id', None)
    if refresh:
        #refresh()
        st.rerun()

def player_ui():
    if 'GAME_ID' not in os.environ:
    #if 'game_id' not in st.session_state:
        game_id = st.text_input("Game ID")
        if st.button("Join game"):
            try:
                response = requests.post(server_root_url+"/check_game_exists", json={"game_id": game_id}, auth=basic_auth)
            except:
                st.write("Error joining game. Is the server up?")
                return
            if response.json().get('game_exists'):
                #st.session_state.game_id = game_id
                os.environ['GAME_ID'] = game_id
                #refresh()
                st.rerun()
            else:
                st.write("Game does not exist!")
    else:
        #if 'player_number' not in st.session_state:
        get_game_status()
        if 'GAME_STATUS' in os.environ:
            if os.environ['GAME_STATUS'] == "Ended":
                st.write("Game has ended, please join a new game.")
                #reset_session("player")
            else:
                if 'PLAYER_NUMBER' not in os.environ:
                    player_id = st.text_input("Player ID")
                    if st.button("Get number"):
                        try:
                            response = requests.post(server_root_url+"/get_number", json={"game_id": os.environ['GAME_ID'], "player_id": player_id, "user_ip": user_ip}, auth=basic_auth)
                        except:
                            st.write("Error getting number. Is the server up?")
                            return
                        os.environ['PLAYER_ID'] = player_id
                        os.environ['PLAYER_NUMBER'] = str(response.json().get('player_number'))
                        #st.session_state.player_id= player_id
                        #st.session_state.player_number = str(response.json().get('player_number'))
                        #refresh()
                        st.rerun()
                else:
                    st.title(os.environ['PLAYER_ID'] + ", your card is: " + os.environ['PLAYER_NUMBER'])
                    image_url = random.choice(images_dict[os.environ['PLAYER_NUMBER']])
                    st.image(image_url,caption=os.environ['PLAYER_NUMBER'])

def game_master_ui():
    st.title("You are the Game Master 🧙‍♂️😙")
    #if 'game_id' not in st.session_state:
    if 'GAME_ID' not in os.environ:
        if st.button("Start new game"):
            try:
                response = requests.post(server_root_url+"/new_game", json={"user_ip": user_ip}, auth=basic_auth)
            except:
                st.write("Error starting new game. Is the server up?")
                return
            print("coucou")
            print(response)
            if response.json().get('result') == "Too many games, please wait":
                st.write("Too many games, please wait")
            elif response.json().get('result') == "Invalid IP address":
                st.write("Invalid IP address")
            else:
                st.write(response.json().get('result'))
                os.environ['GAME_ID'] = response.json().get('result').split("ID: ")[1]
                #st.session_state.game_id = response.json().get('result').split("ID: ")[1]
                #refresh()
                st.rerun()
    else:
        st.write("Game ID: " + os.environ['GAME_ID'])
        st.header("Vote for the players values")
        get_game_players() # run a loop to check for potential player changes
        #if 'players_list' in st.session_state:
        if 'PLAYERS_LIST' in os.environ:
            players_list = json.loads(os.environ['PLAYERS_LIST'])
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
                        response = requests.post(server_root_url+"/guess_all_players", json={"game_id": os.environ['GAME_ID'], "guessed_data": modified_df.to_dict()}, auth=basic_auth)
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
    st.write("Spectator UI")
    if st.button("Get games"):
            try:
                response = requests.post(server_root_url+"/get_games", auth=basic_auth)
            except:
                st.write("Error getting games. Is the server up?")
                return
            st.write(response.json().get('games_data'))
    #if 'game_id' not in st.session_state:
    if 'GAME_ID' not in os.environ:
        game_id = st.text_input("Game ID")
        if st.button("Spectate game"):
            try:
                response = requests.post(server_root_url+"/check_game_exists", json={"game_id": game_id}, auth=basic_auth)
            except:
                st.write("Error checking game. Is the server up?")
                return
            if response.json().get('game_exists'):
                #st.session_state.game_id = game_id
                os.environ['GAME_ID'] = game_id
                #refresh()
                st.rerun()
            else:
                st.write("Game does not exist!")
    else:
        if st.button("Get all numbers"):
            #response = requests.post(server_root_url+"/all_numbers", json={"game_id": st.session_state.game_id})
            try:
                response = requests.post(server_root_url+"/all_numbers", json={"game_id": os.environ['GAME_ID']}, auth=basic_auth)
            except:
                st.write("Error getting all numbers. Is the server up?")
                return
            st.write(response.json().get('player_numbers'))
        if st.button("Get players"):
            try:
                response = requests.post(server_root_url+"/get_players", json={"game_id": os.environ['GAME_ID']}, auth=basic_auth)
            except:
                st.write("Error getting players data. Is the server up?")
                return
            st.write(response.json().get('players_data'))
        if st.button("Get guessing status"):
            try:
                response = requests.post(server_root_url+"/debug_get_guessing_status", json={"game_id": os.environ['GAME_ID']}, auth=basic_auth)
            except:
                st.write("Error getting guessing status. Is the server up?")
                return
            st.write(response.json().get('guessing_status'))

#def refresh():
#    js_script = "reload()"
#    st_javascript(js_script)

if 'USER_TYPE' not in os.environ:
#if 'user_type' not in st.session_state:
    # Define user type
    option = st.selectbox(
        "User type",
        ("Player", "Game Master", "Spectator"),
        index=None,
        placeholder="Pick your user type",
    )

    if option == "Player":
        #st.session_state.user_type = "player"
        os.environ['USER_TYPE'] = "player"     
        #refresh()
        st.rerun()
    elif option == "Game Master":
        #st.session_state.user_type = "game_master"
        os.environ['USER_TYPE'] = "game_master"
        #refresh()
        st.rerun()
    elif option == "Spectator":
        #st.session_state.user_type = "spectator"
        os.environ['USER_TYPE'] = "spectator"
        #refresh()
        st.rerun()
else:
    #if st.session_state.user_type == "player":
    if os.environ['USER_TYPE'] == "player":
        if st.button("Back"):
            reset_session("player")
        player_ui()
    elif os.environ['USER_TYPE'] == "game_master":
        if st.button("Back"):
            reset_session("game_master")
        game_master_ui()
    elif os.environ['USER_TYPE'] == "spectator":
        if st.button("Back"):
            reset_session("spectator")
        spectator_ui()
    else:
        st.write("Invalid user type, please refresh and reset your cache (Ctrl+F5)")
