import socket
import time as t
import re
import csv
import json
import requests

HOST = "irc.chat.twitch.tv"
PORT = 6667
NICK = "gustavesbot"
PASS = "oauth:lcydpwtchpthnvxwu84e77opbefys3"
CHAN = "#gustaves_"

commands = {}
minerals = {}

bet_minerals = {}
bet_team = {}

last_winner = 0

last_time = 60

def nl():
    print("\n")

nl()

with open("commands.csv") as file:
    for row in csv.reader(file, delimiter=','):
        if row[0] == r'\break':
            break
        commands[row[0]] = row[1]
        print(', '.join(row))
    nl()

with open("minerals.csv") as file:
    for row in csv.reader(file, delimiter=':'):
        minerals[row[0]] = row[1]
        print(', '.join(row))
    nl()

def check_users():
    data = requests.get('https://tmi.twitch.tv/group/user/gustaves_/chatters')

    for types in data.json()['chatters']:
        for name in data.json()['chatters'][types]:
            if not name in minerals.keys():
                minerals[name] = 0

def update_csv():
    with open("minerals.csv", 'w+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_NONE, escapechar=' ', lineterminator='\n')
        for data in minerals:
            writer.writerow([data +  ':' + str(minerals[data])])

def add_minerals():
    print(t.gmtime())
    global last_time
    if t.gmtime()[4] != last_time:
        last_time = t.gmtime()[4]
        for key in minerals.keys():
            minerals[key] = str(int(minerals[key]) + 5)

def bet(user, amount, team):
    print('{} bet {} on {}'.format(user, amount, team))

s = socket.socket()
s.connect((HOST, PORT))
s.setblocking(False)

s.send("PASS {}\r\n".format(PASS).encode("utf-8"))
s.send("NICK {}\r\n".format(NICK).encode("utf-8"))
s.send("JOIN {}\r\n".format(CHAN).encode("utf-8"))

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

while True:
    check_users()
    add_minerals()
    update_csv()
    try:
        server_message_received = s.recv(1024).decode("utf-8")
        print(server_message_received)
        if server_message_received == "PING: tmi.twitch.tv\r\n":
            s.send("PONG: tmi.twitch.tv\r\n")
        else:
            compiled_message = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
            if server_message_received: username = re.search(r"\w+", server_message_received).group(0)
            text_message_received = compiled_message.sub("", server_message_received)
            if username != "tmi":
                print(t.strftime('%H:%M:%S', t.gmtime()) + ": " + username + ": " + text_message_received)
                words_in_message = text_message_received.split(' ')
                next_word_minerals = False
                next_word_team = False
                next_word_winner = False
                bet_command_complete = False
                winner_command_complete = False
                for word_in_message in words_in_message:
                    word_in_message = word_in_message.rstrip()
                    if is_command(word_in_message):
                        print(word_in_message + " is a command\n")

                        variables = {'#user': "@" + username,
                                     '#minerals': minerals[username] if username in minerals.keys() else '0',
                                     '#betminerals': bet_minerals[username],
                                     '#team': bet_team[username]}

                        if word_in_message == '!bet':
                            next_word_minerals = True
                        elif next_word_minerals == True:
                            bet_minerals[username] = word_in_message
                            new_minerals = str(int(minerals[username]) - int(word_in_message))
                            minerals[username] = new_minerals
                            next_word_team = True
                            next_word_minerals = False
                        elif next_word_team == True:
                            bet_team[username] = word_in_message
                            bet_command_complete = True
                            next_word_team = False
                        elif word_in_message == '!winner':
                            next_word_winner = True
                        elif next_word_winner == True:
                            last_winner = word_in_message
                            for user in bet_team.keys():
                                if bet_team[user] == last_winner:
                                    del bet_team[user]
                                    new_minerals = str(int(minerals[user]) + int(bet_minerals[user]))
                                    del bet_minerals[user]
                                    minerals[user] = new_minerals
                                else:
                                    del bet_team[user]
                                    new_minerals = str(int(minerals[user]) - int(bet_minerals[user]))
                                    del bet_minerals[user]
                                    minerals[user] = new_minerals
                            next_word_winner = False
                        else:
                            respond(word_in_message, variables)

                        if bet_command_complete:
                            respond('!bet', variables)
                            bet_command_complete = False
                        elif winner_command_complete:
                            respond('!winner', variables)
                            winner_command_complete = False
    except IOError as e:
        print('no message received')
    t.sleep(0.1)
