#/usr/bin/python3
import socket
import sys
import time
import re
import random
import linecache
import html 
import threading
from datetime import datetime,date
tweetnum = 922321981
interval = 2000
next_msg = time.time() + 500  # unix timestamp of next time to post

def RandomDrilTweet(irc, channel):
    driltxt = open('dril.txt') 
    num_lines = sum(1 for line in driltxt)
    linenum = random.randint(1, num_lines)
    line = linecache.getline('dril.txt', linenum)
    matchObj = re.search('(\d+)\|([^\|]+)\|(.*)', line)
    while re.search('(\d{4}\|(RT )?@)|fag|nigg(a|er)|retard', line, re.IGNORECASE) or not(matchObj):    # don't post retweets, replies, or anything with slurs
        linenum = random.randint(1, num_lines)
        line = linecache.getline('dril.txt', linenum)
        line = html.unescape(line)
        matchObj = re.search('(\d+)\|([^\|]+)\|(.*)', line)
    driltxt.close()
    print("linenum: " + str(linenum))
    IrcSend("PRIVMSG " + channel + " :" + matchObj.group(3), irc)
    global tweetnum
    tweetnum = matchObj.group(1)

def DrilTweetLoop(irc, channel):
    while 1:
        time.sleep(1)
        global next_msg
        while (next_msg > time.time()):
            time.sleep(1)
        RandomDrilTweet(irc, channel)
        next_msg = time.time() + interval

def IrcSend(string, irc):
    ts = time.time()
    st = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    if re.search("^PRIVMSG NickServ :IDENTIFY ", string):
        print(st + " [ IRC ] --> PRIVMSG NickServ :IDENTIFY *****")
    else:
        print(st + " [ IRC ] --> " + string)
    irc.send(bytes(string + "\r\n", "utf-8"))

def IsRegistered(nick, irc):
    IrcSend("WHO " + nick, irc)
    text = irc.recv(2048).decode('utf-8')
    ts = time.time()
    st = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    for line in text.split('\r\n'):
        print(st + " [ IRC ] <-- " + line)
        if re.search("352 [^ ]+ [^ ]+ [^ ]+ [^ ]+ [^ ]+ " + nick + " [^ ]*r[^ ]* ", line.split(":")[1]):
            return True
        else:
            IrcSend("PRIVMSG " + nick + " :Error: you must be registered with NickServ to use admin commands.", irc)
            return False

def IrcBot(server, channel, botnick):
    passfile = open('password.txt')
    botpass = passfile.read()
    passfile.close()
    ts = time.time()
    st = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(st + " [ IRC ] connecting to: " + server)
    irc.connect((server, 6667))
    IrcSend("USER " + botnick +" "+ botnick +" "+ botnick +" :no", irc)
    IrcSend("NICK " + botnick, irc)
    lastMessageTime = 0
    joined = False
    tweetLoopProcess = threading.Thread(target=DrilTweetLoop, args=(irc, channel))

    while 1:
        time.sleep(0.01)
        text=irc.recv(2048).decode('utf-8')
        ts = time.time()
        st = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        
        if (text == ''):
            print(st + " [ IRC ] disconnected")
            irc.close()
            return True
        
        for line in text.split('\r\n'):
            print(st + " [ IRC ] <-- " + line)
            global interval
            global next_msg
            if re.search("^PING", line):
                IrcSend("PONG " + line.split(' ')[1], irc)
            elif re.search("001 " + botnick, line):
                IrcSend("JOIN "+ channel, irc)
                IrcSend("PRIVMSG NickServ :IDENTIFY " + botpass, irc)
                tweetLoopProcess.start()
            elif re.search("^:[^ ]+ PRIVMSG " + channel + ' :' + botnick + '.? (url|link)', line, re.IGNORECASE):
                IrcSend("PRIVMSG " + channel + " :" + "https://twitter.com/dril/status/" + str(tweetnum), irc)
            elif re.search("^:[^ ]+ PRIVMSG " + channel + ' :' + botnick + '.? post', line, re.IGNORECASE):
                RandomDrilTweet(irc, channel)
                next_msg = time.time() + interval
            elif re.search("^:[^ ]+ PRIVMSG " + channel + " :shut up " + botnick, line, re.IGNORECASE):
                IrcSend("PRIVMSG " + channel + " :" + line.split("!")[0][1:] + ": https://twitter.com/dril/status/922321981", irc)
            elif re.search("PRIVMSG " + botnick + ' :(url|link)', line, re.IGNORECASE):
                IrcSend("PRIVMSG " + line.split('!')[0][1:] + " :https://twitter.com/dril/status/" + str(tweetnum), irc)
            elif re.search("^:(tjb0607|tinaun|maryxus|rafe)!.* PRIVMSG " + botnick  + " :interval (\d+)$", line, re.IGNORECASE):
                nick = line.split('!')[0][1:]
                if IsRegistered(nick, irc):
                    interval = int(line.split(' ')[-1])
                    IrcSend("PRIVMSG " + nick + " :interval set to " + str(interval), irc)
            elif re.search("PRIVMSG " + botnick + " :interval", line, re.IGNORECASE):
                IrcSend("PRIVMSG " + line.split('!')[0][1:] + " :interval is " + str(interval), irc)
            elif re.search("^:(tjb0607|tinaun|maryxus|rafe)!.* PRIVMSG " + botnick + " :reset", line, re.IGNORECASE):    # reset timer
                nick = line.split('!')[0][1:]
                if IsRegistered(nick, irc):
                    next_msg = time.time() + interval
                    IrcSend("PRIVMSG " + nick + " :timer reset", irc)
            elif re.search("PRIVMSG " + botnick + " :help", line, re.IGNORECASE):
                IrcSend("PRIVMSG " + line.split('!')[0][1:] + " :`url` returns the url of the last tweet, `post` posts a new random tweet, and `interval` prints the current message interval in seconds. Admin commands are `reset` to reset the timer, and `interval <seconds>` to set the interval. Only tjb0607, tinaun, maryxus, and rafe can use admin commands.", irc)
    return

#IrcBot("irc.synirc.net", "#bottest", "drilbot2")
IrcBot("irc.synirc.net", "#homestuck", "drilbot")
