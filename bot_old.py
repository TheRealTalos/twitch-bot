import socket
import time as t
import re
import csv
import requests
import time

#TODO: fix error when chat inactivity
#TODO: make betting better
#TODO: comment code

s = socket.socket()

HOST = "irc.chat.twitch.tv"
PORT = 6667
NICK = "gustavesbot"
PASS = "oauth:lcydpwtchpthnvxwu84e77opbefys3"
CHAN = "#gustaves_"

commands = {}
minerals = {}
variables = {}

bet_minerals = {}
bet_team = {}

betting = True

last_winner = '0'

last_time = 60

def import_commands():
    with open("commands.csv") as file:
        for row in csv.reader(file, delimiter=','):
            if row[0] == r'\break':
                break
            commands[row[0]] = row[1]

def import_minerals():
    with open("minerals.csv") as file:
        for row in csv.reader(file, delimiter=':'):
            minerals[row[0]] = row[1]

def connect_socket():
    s.connect((HOST, PORT))
    s.setblocking(False)

    s.send("PASS {}\r\n".format(PASS).encode("utf-8"))
    s.send("NICK {}\r\n".format(NICK).encode("utf-8"))
    s.send("JOIN {}\r\n".format(CHAN).encode("utf-8"))

def check_users():
    data = requests.get('https://tmi.twitch.tv/group/user/gustaves_/chatters')

    for types in data.json()['chatters']:
        for name in data.json()['chatters'][types]:
            if not name in minerals.keys():
                minerals[name] = 0

def is_admin(username):
    data = requests.get('https://tmi.twitch.tv/group/user/gustaves_/chatters')

    for name in data.json()['chatters']['moderators']:
        if username == name:
            return True

    return False

def update_csv():
    with open("minerals.csv", 'w+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_NONE, escapechar=' ', lineterminator='\n')
        for data in minerals:
            writer.writerow([data +  ':' + str(minerals[data])])

def add_minerals():
    print(time.gmtime())
    global last_time
    if time.gmtime()[4] != last_time:
        last_time = time.gmtime()[4]
        for key in minerals.keys():
            minerals[key] = str(int(minerals[key]) + 5)

def send(message):
    s.send(("PRIVMSG {} :{}".format(CHAN, message+"\r\n")).encode("utf-8"))

def is_command(command):
    if command in commands:
        return True
    else:
        return False

def respond(word, vars):
    response = commands[word]
    for key in vars.keys():
        response = response.replace(key, variables[key])

    send(response)

def update_vars(username):
    variables = {'#user': "@" + username,
                '#minerals': minerals[username] if username in minerals.keys() else '0',
                '#betminerals': bet_minerals[username] if username in bet_minerals.keys() else '0',
                '#team': bet_team[username] if username in bet_team.keys() else '0',
                '#winningteam': last_winner}


import_commands()
import_minerals()

connect_socket()

while True:
    check_users()
    add_minerals()
    update_csv()
    try:
        server_message_received = s.recv(1024).decode("utf-8")
        if server_message_received == "PING: tmi.twitch.tv\r\n":
            s.send("PONG: tmi.twitch.tv\r\n")
        else:
            compiled_message = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
            if server_message_received: username = re.search(r"\w+", server_message_received).group(0)
            text_message_received = compiled_message.sub("", server_message_received)
            if username != "tmi":
                print(t.strftime('%H:%M:%S', t.gmtime()) + ": " + username + ": " + text_message_received)
                words_in_message = text_message_received.split(' ')
                words_in_message[-1] = words_in_message[-1][:-2]
                words_in_message.append('NULLWORD\r\n')
                print(words_in_message)
                next_word_minerals = False
                next_word_team = False
                next_word_betting = False
                next_word_winner = False
                bet_command_complete = False
                winner_command_complete = False
                for word_in_message in words_in_message:
                    word_in_message = word_in_message.rstrip()
                    if is_command(word_in_message) or next_word_minerals or next_word_team or next_word_minerals \
                            or next_word_betting or next_word_winner or bet_command_complete or winner_command_complete:
                        print(word_in_message + " is a command\n")

                        variables = {'#user': "@" + username,
                                     '#minerals': minerals[username] if username in minerals.keys() else '0',
                                     '#betminerals': bet_minerals[username] if username in bet_minerals.keys() else '0',
                                     '#team': bet_team[username] if username in bet_team.keys() else '0',
                                     '#winningteam': last_winner}

                        if word_in_message == '!bet' and betting:
                            print(1)
                            next_word_minerals = True
                        elif next_word_minerals == True:
                            print(2)
                            if int(word_in_message) <= int(minerals[username]):
                                if username in bet_minerals.keys():
                                    bet_minerals[username] = str(int(bet_minerals[username]) + int(word_in_message))
                                else:
                                     bet_minerals[username] = word_in_message
                                new_minerals = str(int(minerals[username]) - int(word_in_message))
                                minerals[username] = new_minerals
                                next_word_team = True
                            else:
                                send('Not enough minerals. You have {} minerals'.format(minerals[username]))
                            next_word_minerals = False
                        elif next_word_team == True:
                            print(3)
                            bet_team[username] = word_in_message
                            bet_command_complete = True
                            next_word_team = False
                        elif word_in_message == '!betting' and username == 'therealtalos':
                            next_word_betting = True
                        elif next_word_betting:
                            if word_in_message == 'on':
                                betting = True
                                send('Betting is now on')
                                next_word_betting = False
                            elif word_in_message == 'off':
                                betting = False
                                send('Betting is now off')
                                next_word_betting = False
                            else:
                                send('That is not a valid value. Use !betting on/off')
                        elif word_in_message == '!winner' and username == 'therealtalos':
                            next_word_winner = True
                        elif next_word_winner == True:
                            last_winner = word_in_message
                            for user in list(bet_team):
                                if bet_team[user] == last_winner:
                                    del bet_team[user]
                                    new_minerals = str(int(minerals[user]) + int(bet_minerals[user])*2)
                                    del bet_minerals[user]
                                    minerals[user] = new_minerals
                                winner_command_complete = True
                            next_word_winner = False
                        elif not betting:
                            send('Betting is currently off. Please wait for the current game to end to place a bet on the next')
                        elif not word_in_message == '!winner' and not word_in_message == '!betting':
                            respond(word_in_message, variables)

                            variables = {'#user': "@" + username,
                                         '#minerals': minerals[username] if username in minerals.keys() else '0',
                                         '#betminerals': bet_minerals[
                                             username] if username in bet_minerals.keys() else '0',
                                         '#team': bet_team[username] if username in bet_team.keys() else '0',
                                         '#winningteam': last_winner}

                        if bet_command_complete:
                            variables.update()
                            respond('!bet', variables)
                            bet_command_complete = False
                        elif winner_command_complete:
                            variables.update()
                            respond('!winner', variables)
                            winner_command_complete = False
    except IOError as e:
        t.sleep(0.0001)
    t.sleep(0.1)

