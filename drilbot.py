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

def RandomDrilTweet(irc, st, channel):
    driltxt = open('dril.txt') 
    num_lines = sum(1 for line in driltxt)
    linenum = random.randint(1, num_lines) - 1
    line = linecache.getline('dril.txt', linenum)
    while re.search('\d{4}\|(RT )?@', line):
        linenum = random.randint(1, num_lines) - 1
        line = linecache.getline('dril.txt', linenum)
    line = html.unescape(line)
    driltxt.close()
    matchObj = re.search('(\d+)\|([^\|]+)\|(.*)', line)
    IrcSend("PRIVMSG " + channel + " :" + matchObj.group(3), irc, st)
    global tweetnum
    tweetnum = matchObj.group(1)

def DrilTweetLoop(irc, channel):
    while 1:
        time.sleep(1)
        global next_msg
        while (next_msg > time.time()):
            time.sleep(1)
        ts = time.time()
        st = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        RandomDrilTweet(irc, st, channel)
        next_msg = time.time() + interval

def IrcSend(string, irc, st):
    if re.search("^PRIVMSG NickServ :IDENTIFY ", string):
        print(st + " [ IRC ] --> PRIVMSG NickServ :IDENTIFY *****")
    else:
        print(st + " [ IRC ] --> " + string)
    irc.send(bytes(string + "\r\n", "utf-8"))

def IrcBot(server, channel, botnick):
    passfile = open('password.txt')
    botpass = passfile.read()
    passfile.close()
    ts = time.time()
    st = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(st + " [ IRC ] connecting to: " + server)
    irc.connect((server, 6667))
    IrcSend("USER " + botnick +" "+ botnick +" "+ botnick +" :no", irc, st)
    IrcSend("NICK " + botnick, irc, st)
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
                IrcSend("PONG " + line.split(' ')[1], irc, st)
            elif re.search("001 " + botnick, line):
                IrcSend("JOIN "+ channel, irc, st)
                IrcSend("PRIVMSG NickServ :IDENTIFY " + botpass, irc, st)
                tweetLoopProcess.start()
            elif re.search("PRIVMSG " + channel + ' :' + botnick + ': url', line, re.IGNORECASE):
                IrcSend("PRIVMSG " + channel + " :" + "https://twitter.com/dril/status/" + str(tweetnum), irc, st)
            elif re.search("PRIVMSG " + channel + ' :' + botnick + ': post', line, re.IGNORECASE):
                RandomDrilTweet(irc, st, channel)
                next_msg = time.time() + interval
            elif re.search("PRIVMSG " + botnick + ' :url', line, re.IGNORECASE):
                IrcSend("PRIVMSG " + line.split('!')[0][1:] + " :https://twitter.com/dril/status/" + str(tweetnum), irc, st)
            elif re.search("^:(tjb0607|tinaun|maryxus|rafe)!.* PRIVMSG " + botnick  + " :interval (\d+)$", line, re.IGNORECASE):
                interval = int(line.split(' ')[-1])
                IrcSend("PRIVMSG " + line.split('!')[0][1:] + " :interval set to " + str(interval), irc, st)
            elif re.search("PRIVMSG " + botnick + " :interval", line, re.IGNORECASE):
                IrcSend("PRIVMSG " + line.split('!')[0][1:] + " :interval is " + str(interval), irc, st)
            elif re.search("^:(tjb0607|tinaun|maryxus|rafe)!.* PRIVMSG " + botnick + " :reset", line, re.IGNORECASE):    # reset timer
                next_msg = time.time() + interval
                IrcSend("PRIVMSG " + line.split('!')[0][1:] + " :timer reset", irc, st)
            elif re.search("PRIVMSG " + botnick + " :help", line, re.IGNORECASE):
                IrcSend("PRIVMSG " + line.split('!')[0][1:] + " :`url` returns the url of the last tweet, `post` posts a new random tweet, and `interval` prints the current message interval in seconds. Admin commands are `reset` to reset the timer, and `interval <seconds>` to set the interval. Only tjb0607, tinaun, maryxus, and rafe can use admin commands.", irc, st)
    return

#IrcBot("irc.synirc.net", "#bottest", "drilbot2")
IrcBot("irc.synirc.net", "#homestuck", "drilbot")
