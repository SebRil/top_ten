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
from openai import OpenAI

print('####### RUNNING INSTANCE #######')
st.set_page_config(page_title='Top Ten ADeVeP', layout='wide')

# Setting global vars
global server_root_url
#server_root_url = "http://localhost:5000"
server_root_url = "https://sebril.pythonanywhere.com"
global basic_auth
if server_root_url == "http://localhost:5000":
    basic_auth=None
else:
    basic_auth = HTTPBasicAuth(st.secrets['PY_ANYWHERE_USER'], st.secrets['PY_ANYWHERE_PW'])
global watson_api_key
global watson_api_url
watson_api_key=st.secrets['WATSON_API_KEY']
watson_api_url=st.secrets['WATSON_API_URL']
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
    if not in_env('GAME_THEME'):
        set_env_var('GAME_THEME', '')

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

@st.dialog("Information")
def show_popup(text):
    st.write(text)

@st.dialog("Error")
def show_error(text):
    st.write(text)

@st.dialog('Sorry, you failed')
def show_results_popup(text):
    st.write("Unfortunately you made at least one mistake, see results below:")
    st.dataframe(text)
    st.write("The game will now end, please start a new one.")

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
def get_game_info():
    print('Running fragment get_game_info')
    if in_env('GAME_ID'):
        print('Getting game status')
        try:
            response = requests.post(server_root_url+"/check_game_exists", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
        except:
            game_status_loc = "Ended"
        if response.json().get('game_exists'):
            game_status_loc = "Ongoing"
        else:
            game_status_loc = "Ended"
        print('Getting game players')
        try:
            response = requests.post(server_root_url+"/get_players", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
        except:
            other_players_loc = []
        other_players_loc=response.json().get('players_data')
        if not in_env('GAME_STATUS'):
            print('refreshing after creating game status')
            set_env_var('GAME_STATUS', game_status_loc)
            set_env_var('OTHER_PLAYERS', other_players_loc)
            st.rerun()
        if get_env('GAME_STATUS') != game_status_loc and get_env('OTHER_PLAYERS') == other_players_loc:
            print('refreshing 2')
            set_env_var('GAME_STATUS', game_status_loc)
            st.rerun()
        elif get_env('GAME_STATUS') != game_status_loc and get_env('OTHER_PLAYERS') != other_players_loc:
            print('refreshing 3')
            set_env_var('GAME_STATUS', game_status_loc)
            set_env_var('OTHER_PLAYERS', other_players_loc)
            st.rerun()
        elif get_env('GAME_STATUS') == game_status_loc and get_env('OTHER_PLAYERS') != other_players_loc:
            print(get_env('OTHER_PLAYERS'))
            print('refreshing 4')
            print(other_players_loc)
            set_env_var('OTHER_PLAYERS', other_players_loc)
            print(get_env('OTHER_PLAYERS'))
            st.rerun()

def reset_session(caller,refresh=True):
    print("Reset cache initiated by " + caller)
    if caller == "game_master":
        try:
            requests.post(server_root_url+"/destroy_game", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
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
    if in_env('OTHER_PLAYERS'):
        del_env_var('OTHER_PLAYERS')
    if in_env('GAME_THEME'):
        del_env_var('GAME_THEME')
    if refresh:
        st.rerun()

def player_ui():
    st.title("You are a Player 🃏")
    if not in_env('GAME_ID') and not in_env('PLAYER_ID') and not in_env('PLAYER_NUMBER'):
        print('Offering to join a game')
        game_id = st.text_input("Game ID")
        player_id = st.text_input("Player ID")
        if st.button("Join game"):
            try:
                response = requests.post(server_root_url+"/check_game_exists", json={"game_id": game_id}, auth=basic_auth)
            except:
                st.write("Error checking game. Is the server up?")
                return
            print(response.json().get('game_exists'))
            if response.json().get('game_exists'):
                try:
                    response = requests.post(server_root_url+"/get_player_data", json={"game_id": game_id, "player_id": player_id, "user_ip": user_ip}, auth=basic_auth)
                except:
                    st.write("Error getting number. Is the server up?")
                    return
                if response.json().get('player_number') == "Player ID already exists!.":
                    st.write("Player ID already exists!")
                elif str(response.json().get('player_number')).startswith("You are already connected"):
                    st.write(response.json().get('player_number'))
                else:
                    set_env_var('GAME_ID', game_id)
                    set_env_var('PLAYER_ID', player_id)
                    set_env_var('PLAYER_NUMBER', str(response.json().get('player_number')))
                    set_env_var('GAME_THEME', str(response.json().get('game_theme')))
                    #st_javascript('reload()')
                    st.rerun()
            else:
                st.write("Game does not exist!")
    else:
        get_game_info()
        if in_env('GAME_STATUS'):
            if get_env('GAME_STATUS') == "Ended":
                show_popup("Game has ended, please join a new game.")
            else:
                col1, col2 = st.columns([0.8,0.2])
                player_id = get_env('PLAYER_ID')
                with col1:
                    st.header("The theme of this game is: " + get_env('GAME_THEME'))
                    st.write(player_id + ", your card is: " + get_env('PLAYER_NUMBER'))
                    image_url = random.choice(images_dict[get_env('PLAYER_NUMBER')])
                    st.image(image_url,caption=get_env('PLAYER_NUMBER'))
                with col2:
                    st.header('Other players')
                    if in_env('OTHER_PLAYERS'):
                        other_players_1 = get_env('OTHER_PLAYERS').copy()
                        if player_id in other_players_1:
                            other_players_1.remove(player_id)
                        if other_players_1 != []:
                            df = pd.DataFrame(other_players_1,columns=['Username'])
                            st.dataframe(
                                other_players_1,
                                use_container_width=True,
                                hide_index =True
                            )
                        else:
                            st.write("Waiting for other players...")
        else:
            show_error("The game status couldn't be found. This error should never happen, please contact the developer.")

def game_master_ui():
    st.title("You are the Game Master 🧙‍♂️")
    if not in_env('GAME_ID'):
        st.header("Game settings")
        st.write("What will be the theme of this game?")
        col1, col2 = st.columns([0.7,0.3])
        with st.container():
            with col1:
                game_theme = st.text_input(label='',value=get_env('GAME_THEME'),label_visibility="collapsed")
                set_env_var('GAME_THEME',game_theme)
                st.write("How many players will there be?")                
                player_count = st.number_input(label='',label_visibility="collapsed",max_value=10,min_value=1)
            with col2:
                if st.button("Generate theme"):
                    client = OpenAI(
                        api_key=st.secrets['API_KEY']
                    )
                    completion = client.chat.completions.create(
                        model="gpt-4o-mini",
                        store=True,
                        messages=[
                            {"role": "user", "content": "Generate a theme similar to this: 'Your best vacation destination' or 'Your best childhood memory' etc. Keep the answer extra short."},
                        ]
                    )
                    set_env_var('GAME_THEME', completion.choices[0].message.content.replace('\'',''))
                    st.rerun()
        if st.button("Start new game"):
            if get_env('GAME_THEME') == '' or get_env('GAME_THEME').isspace():
                show_error("Please define a game theme before starting")
            else:
                try:
                    response = requests.post(server_root_url+"/new_game", json={"user_ip": user_ip,"game_theme": get_env('GAME_THEME'),"player_count":player_count}, auth=basic_auth)
                except:
                    st.write("Error starting new game. Is the server up?")
                    return
                if response.json().get('result') == "Too many games, please wait":
                    st.write("Too many games, please wait")
                elif response.json().get('result') == "Invalid IP address":
                    st.write("Invalid IP address")
                else:
                    #st.write(response.json().get('result'))
                    set_env_var('GAME_ID', response.json().get('result').split("ID: ")[1])
                    #st_javascript('reload()')
                    st.rerun()
    else:
        st.write("Game ID: " + get_env('GAME_ID'))
        st.write("Game theme: " + get_env('GAME_THEME'))
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
                        show_popup("Congratulations! All values are correct. The game will now end, please start a new one.")
                        #st.write("Congratulations! All values are correct. The game will now end, please start a new one.")
                        reset_session("game_master",refresh=False)
                    else:
                        #show_popup("Unfortunately you made at least one mistake, see results below:")
                        show_results_popup(response.json().get('guessing_status'))
                        #st.write(response.json().get('guessing_status'))
                        #st.write("The game will now end, please start a new one.")
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

########################### MAIN ###########################
# Get current user's ip and initialize environment
global user_ip
user_ip = get_remote_ip()
initialize_env()
print(curr_env)

st.sidebar.title('Top Ten ADeVeP')
#st.sidebar.divider()

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
        if st.sidebar.button("🏠 Home"):
            reset_session("player")
        player_ui()
    elif get_env('USER_TYPE') == "game_master":
        if st.sidebar.button("🏠 Home"):
            reset_session("game_master")
        game_master_ui()
    elif get_env('USER_TYPE') == "spectator":
        if st.sidebar.button("🏠 Home"):
            reset_session("spectator")
        spectator_ui()
    else:
        st.write("Invalid user type, please refresh and reset your cache (Ctrl+F5)")