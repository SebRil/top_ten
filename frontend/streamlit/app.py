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

# TODO: Rejoindre la partie d'abord PUIS pick le game master au pif + enchaîner partie avec un roulement du game master
# TODO: Ajouter des coches "qui a parlé" dans le tableau des joueurs

print('####### RUNNING INSTANCE - B #######')
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
        print(curr_env)
    #if not in_env('GAME_THEME'):
    #    set_env_var('GAME_THEME', '')

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
    # Needs to set game theme as well
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
        print('Getting game theme')
        try:
            response = requests.post(server_root_url+"/get_game_theme", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
        except:
            print('Error getting game theme')
        set_env_var('GAME_THEME',response.json().get('game_theme'))

@st.fragment(run_every=1)
def get_game_members():
    print('Running fragment get_game_members')
    if in_env('GAME_ID'):
        print('Getting members')
        try:
            response = requests.post(server_root_url+"/get_members", json={"game_id": get_env('GAME_ID')}, auth=basic_auth)
        except:
            show_error('Error getting players (server not up?)')
            return
        if response.status_code != 200:
            show_error('Error getting players')
            return
        else:
            players = []
            game_master = ''
            for member in response.json().get('members'):
                if member['user_type'] == 'player':
                    players.append(member['username'])
                elif member['user_type'] == 'game_master':
                    game_master = member['username']
            if (not in_env('PLAYERS_LIST') and players != []) or (json.dumps(players) != get_env('PLAYERS_LIST')):
                print('Updating members list')
                set_env_var('PLAYERS_LIST', json.dumps(players))
                st.rerun()
            elif in_env('PLAYERS_LIST') and json.dumps(players) != get_env('PLAYERS_LIST'):
                print('Updating members list')
                set_env_var('PLAYERS_LIST', json.dumps(players))
                st.rerun()
            if not in_env('GAME_MASTER') and game_master != '':
                print('Updating Game Master')
                set_env_var('GAME_MASTER', game_master)
                st.rerun()
            elif in_env('GAME_MASTER') and  game_master != get_env('GAME_MASTER'):
                print('Updating Game Master')
                set_env_var('GAME_MASTER', game_master)
                st.rerun()

def reset_session(kill_game=False,refresh=True):
    print("Reset cache")
    try:
        requests.post(server_root_url+"/leave_game", json={"game_id": get_env('GAME_ID'),'user_ip':user_ip}, auth=basic_auth)
    except:
        print("Error leaving the game. Is the server up?")
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
    if in_env('USERNAME'):
        del_env_var('USERNAME')
    if in_env('PLAYERS_LIST'):
        del_env_var('PLAYERS_LIST')
    if in_env('GAME_MASTER'):
        del_env_var('GAME_MASTER')
    if refresh:
        st.rerun()

def player_ui():
    st.title("You are a Player 🃏")
    get_game_info()
    if not in_env('GAME_STATUS'):
        st.text('Waiting for the game master to start the game')
    else:
        if in_env('GAME_STATUS'):
            if get_env('GAME_STATUS') == "Ended":
                show_popup("Game has ended, please join a new game.")
            else:
                st.title("Game Theme")
                if in_env('GAME_THEME'):
                    st.text(get_env('GAME_THEME'))
                else:
                    st.text('The Game Master still needs to pick a theme.')
                st.divider()
                if not in_env('PLAYER_NUMBER'):
                    if st.button('Draw a card'):
                        if not in_env('GAME_THEME'):
                            show_popup('You cannot draw a card until the game master has decided on a theme')
                        try:
                            response = requests.post(server_root_url+"/draw_card", json={"game_id": get_env('GAME_ID'),"username":get_env('USERNAME'),"user_ip": user_ip}, auth=basic_auth)
                        except:
                            st.write("Error. Is the server up?")
                            return
                        if not response.json().get('success'):
                            st.write(response.json().get('message'))
                        else:
                            set_env_var('PLAYER_NUMBER', response.json().get('value'))
                            st.rerun()
                else:
                    st.write("Your card is: " + get_env('PLAYER_NUMBER'))
                    image_url = random.choice(images_dict[get_env('PLAYER_NUMBER')])
                    st.image(image_url,caption=get_env('PLAYER_NUMBER'))
                        
        else:
            show_error("The game status couldn't be found. This error should never happen, please contact the developer.")

def game_master_ui():
    st.title("You are the Game Master 🧙‍♂️")
    if not in_env('GAME_STATUS'):
        st.header("Game settings")
        st.write("What will be the theme of this game?")
        col1, col2 = st.columns([0.7,0.3])
        if not in_env('GAME_THEME'):
            set_env_var('GAME_THEME', '')
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
                            {"role": "user", "content": "Generate a theme similar to this: 'Your best vacation destination' or 'Your best childhood memory' etc. There  Keep the answer extra short."},
                        ]
                    )
                    set_env_var('GAME_THEME', completion.choices[0].message.content.replace('\'',''))
                    st.rerun()
        if st.button("Start new game"):
            if get_env('GAME_THEME') == '' or get_env('GAME_THEME').isspace():
                show_error("Please define a game theme before starting")
            else:
                try:
                    response = requests.post(server_root_url+"/start_game", json={"game_id": get_env('GAME_ID'),"user_ip": user_ip,"game_theme": get_env('GAME_THEME'),"player_count":player_count}, auth=basic_auth)
                except:
                    st.write("Error starting new game. Is the server up?")
                    return
                if not response.json().get('success'):
                    st.write(response.json().get('message'))
                else:
                    set_env_var('GAME_STATUS', 'Started')
                    st.rerun()
    else:
        st.write("Game theme: " + get_env('GAME_THEME'))
        st.header("Vote for the players values")
        if in_env('PLAYERS_LIST'):
            players_list = json.loads(get_env('PLAYERS_LIST'))
            print(players_list)
            if len(players_list)== 0:
                st.write("Waiting for players to join the game...")
            else:
                list_for_df = []
                for player in players_list:
                    dict_for_df = {}
                    dict_for_df['username'] = player
                    dict_for_df['player_value'] = ''
                    list_for_df += [dict_for_df]
                df = pd.DataFrame(list_for_df)
                modified_df = st.data_editor(
                    df,
                    column_config={
                        "username": st.column_config.Column(
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
                        #reset_session("game_master",refresh=False)
                    else:
                        show_results_popup(response.json().get('guessing_status'))
                        #reset_session("game_master",refresh=False)

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

def welcome_ui():
    with st.container():
        col1, col2, col3 = st.columns([0.4,0.2,0.4])
        with col2:
            st.markdown("<h1 style='text-align: center;'>Top Ten ADeVeP</h1>", unsafe_allow_html=True)
            st.image("./resources/welcome_image.jpg")
            username = st.text_input("Username")
            st.divider()
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([0.45,0.05,0.07,0.18,0.35])
        with col2:
            st.text("Game ID")
        with col3:
            game_id = st.text_input(label='',label_visibility='collapsed')
        with col4:
            if st.button("Join Game"):
                if username == '' or username.isspace():
                    show_error('Please enter a valid username')
                    return
                try:
                    response = requests.post(server_root_url+"/join_game", json={"game_id": game_id,'user_ip':user_ip,'username':username}, auth=basic_auth)
                except:
                    st.write("Error joining game. Is the server up?")
                    return
                if response.json().get('success'):
                    set_env_var('GAME_ID',game_id)
                    set_env_var('USERNAME',username)
                    set_env_var('PLAYER_TYPE',username)
                    st.rerun()
                else:
                    st.write("This game ID doesn't exist")
                    return
    with st.container():
        col1, col2, col3 = st.columns([0.45,0.1,0.45])
        with col2:
            if st.button("Create Game"):
                if username == '' or username.isspace():
                    show_error('Please enter a valid username')
                    return
                try:
                    response = requests.post(server_root_url+"/new_game", json={"user_ip": user_ip,"username":username}, auth=basic_auth)
                except:
                    show_error("Error starting new game. Is the server up?")
                    return
                if not response.json().get('success'):
                    show_error(response.json().get('message'))
                else:
                    set_env_var('GAME_ID', response.json().get('game_id'))
                    set_env_var('USER_TYPE','player')
                    st.rerun()

def player_type_selection_ui():
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

def become_game_master():
    try:
        print('Sending post request with params : ' + get_env('GAME_ID' + ' ' + user_ip + ' ' + get_env('USERNAME')))
        response = requests.post(server_root_url+"/set_game_master", json={"game_id": get_env('GAME_ID'),"user_ip":user_ip,"user_id":get_env('USERNAME')}, auth=basic_auth)
    except:
        show_error('Error GM (server not up?)')
        return
    if response.json().get('success'):
        set_env_var('USER_TYPE','game_master')
        st.rerun()
    else:
        show_error(response.json().get('message'))
        return

def become_player():
    try:
        response = requests.post(server_root_url+"/unset_game_master", json={"game_id": get_env('GAME_ID'),"user_ip":user_ip,"user_id":get_env('USERNAME')}, auth=basic_auth)
    except:
        show_error('Error (server not up?)')
        return
    if response.json().get('success'):
        set_env_var('USER_TYPE','player')
        st.rerun()
    else:
        show_error(response.json().get('message'))
        return

########################### MAIN ###########################
# Get current user's ip and initialize environment
global user_ip
user_ip = get_remote_ip()
initialize_env()

if not in_env('GAME_ID'):
    welcome_ui()
else:
    get_game_members()
    # Handle side bar
    with st.sidebar:
        if st.button("🏠 Home"):
            reset_session(refresh=True)
        st.header('Game ID: ' + get_env('GAME_ID'))
        st.divider()
        st.header('Game Master')
        if in_env('GAME_MASTER') and get_env('GAME_MASTER') != '':
            st.write(get_env('GAME_MASTER'))
        else:
            if st.button('Join'):
                become_game_master()
        st.divider()
        st.header('Players')
        if in_env('PLAYERS_LIST') and get_env('PLAYERS_LIST') != []:
            st.write(player for player in json.loads(get_env('PLAYERS_LIST')))
        if in_env('USER_TYPE') and get_env('USER_TYPE') == 'game_master':
            if st.button('Join'):
                become_player()
    if in_env('USER_TYPE'):
        # Handle main board
        if get_env('USER_TYPE') == "player":
            player_ui()
        elif get_env('USER_TYPE') == "game_master":
            game_master_ui()
        elif get_env('USER_TYPE') == "spectator":
            spectator_ui()
        else:
            st.write("Invalid user type, please refresh and reset your cache (Ctrl+F5)")
