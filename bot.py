import socket
import time as t
import re
import csv
import requests
import time

#TODO: fix that random error that makes no sense and is not reproducible wtf k
#TODO: comment code

s = socket.socket()

HOST = "irc.chat.twitch.tv"
PORT = 6667
NICK = "gustavesbot"
PASS = ""
CHAN = "#gustaves_"

commands = {}
minerals = {}
variables = {}

bet_minerals = {}
bet_team = {}

betting = False

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
#    print(time.gmtime())
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
                words = text_message_received.split(' ')

                print(words)

                for i in range(len(words)):
                    words[i] = words[i].rstrip()

                for i in range(len(words)):
                    if is_command(words[i]):
                        print(words[i] + " is a command\n")

                        variables = {'#user': "@" + username,
                                     '#minerals': minerals[username] if username in minerals.keys() else '0',
                                     '#betminerals': bet_minerals[username] if username in bet_minerals.keys() else '0',
                                     '#team': bet_team[username] if username in bet_team.keys() else '0',
                                     '#winningteam': last_winner}

                        if words[i] == '!bet':
                            if betting:
                                try:
                                    a = words[i+1]
                                    a = words[i+2]
                                    del a

                                    if int(words[i+1]) <= int(minerals[username]):
                                        if username in bet_minerals.keys():
                                            bet_minerals[username] = str(int(bet_minerals[username]) + int(words[i+1]))
                                        else:
                                             bet_minerals[username] = words[i+1]
                                        minerals[username] = str(int(minerals[username]) - int(words[i+1]))
                                        if words[i+2] == 'win' or words[i+2] == 'loss':
                                            bet_team[username] = words[i+2]

                                            variables = {'#user': "@" + username,
                                                         '#minerals': minerals[
                                                             username] if username in minerals.keys() else '0',
                                                         '#betminerals': bet_minerals[
                                                             username] if username in bet_minerals.keys() else '0',
                                                         '#team': bet_team[
                                                             username] if username in bet_team.keys() else '0',
                                                         '#winningteam': last_winner}
                                            respond('!bet', variables)
                                        else:
                                            send('That is not a valid value. Use !bet [amount] [win/loss]')
                                    else:
                                        send('Not enough minerals. You have {} minerals'.format(minerals[username]))

                                except:
                                    send('That is not a valid value. Use !bet [amount] [win/loss]')
                            else:
                                send('Betting is currently off. Please wait for the current game to end to place a bet on the next')

                        elif words[i] == '!betting' and username == 'therealtalos':
                            if words[i+1] == 'on':
                                betting = True
                                send('Betting is now on')
                            elif words[i+1] == 'off':
                                betting = False
                                send('Betting is now off')
                            else:
                                send('That is not a valid value. Use !betting [on/off]')

                        elif words[i] == '!winner' and username == 'therealtalos':
                            last_winner = words[i+1]
                            for user in list(bet_team):
                                if bet_team[user] == last_winner:
                                    del bet_team[user]
                                    new_minerals = str(int(minerals[user]) + int(bet_minerals[user])*2)
                                    del bet_minerals[user]
                                    minerals[user] = new_minerals

                                variables = {'#user': "@" + username,
                                             '#minerals': minerals[
                                                 username] if username in minerals.keys() else '0',
                                             '#betminerals': bet_minerals[
                                                 username] if username in bet_minerals.keys() else '0',
                                             '#team': bet_team[
                                                 username] if username in bet_team.keys() else '0',
                                             '#winningteam': last_winner}

                                respond('!winner', variables)

                        elif not words[i] == '!winner' and not words[i] == '!betting':
                            variables = {'#user': "@" + username,
                                         '#minerals': minerals[
                                             username] if username in minerals.keys() else '0',
                                         '#betminerals': bet_minerals[
                                             username] if username in bet_minerals.keys() else '0',
                                         '#team': bet_team[
                                             username] if username in bet_team.keys() else '0',
                                         '#winningteam': last_winner}
                            respond(words[i], variables)

    except IOError as e:
        t.sleep(0.0001)
    t.sleep(0.1)

