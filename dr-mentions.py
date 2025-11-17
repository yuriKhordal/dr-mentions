from desktop_notifier import DesktopNotifier, Button, Icon
from feedparser import parse
from feedparser.datetimes import _parse_date
from platformdirs import user_config_dir
from config import getConfig, updateMention, initConfig, _isEmptyOrSpace
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
RSS_URL = 'https://static.molodetz.nl/dr.mentions.xml'
# DEFAULT_CONFIG_PATH = '/opt/dr-mentions/dr-mentions.conf'
DEFAULT_CONFIG_PATH = os.path.join(user_config_dir(), 'dr-mentions.conf')
# ICON_PATH = '/home/yuri/Programming/python/devrant-mentions/logo.png'
ICON_PATH = os.path.join(SCRIPT_DIR, 'icon.png')
SLEEP = 90

notifier = DesktopNotifier('devRant Mentions', Icon(uri=ICON_PATH))

async def sendNotif(mention: str, summary: str, link: str, all: bool = False):
    from webbrowser import open

    if (all):
        title = mention.replace('@', '') + 'in a comment!'
    else:
        author = mention[:mention.find(' mentioned @')]
        title = author + ' mentioned you in a comment!'
    
    await notifier.send(
        title=title,
        message=summary.replace('&quot;', '"') + "\n" + link,
        buttons=[Button("Open in Browswer", lambda: open(link))],
        on_clicked=lambda: open(link)
    )

def sendNotifCli(mention: str, summary: str, link: str, all: bool = False):
    if (all):
        title = mention.replace('@', '') + 'in a comment!'
    else:
        author = mention[:mention.find(' mentioned @')]
        title = author + ' mentioned you in a comment!'

    header = f' 🔴 {title}    '
    print('-' * len(header))
    print(header)
    print('-' * len(header))
    print(' ' + summary.replace('&quot;', '"'))
    print(f' 🔗 {link}')

async def rss_listen(ctx):
    from time import sleep
    from asyncio import CancelledError
    import asyncio

    etag: str = None
    prevRssMod: str = None
    stop: bool = False

    strLastMention = ctx['lastMention']
    lastMention = _parse_date(strLastMention)

    # i = 1
    # RSS_URL = open('rss-1.xml').read()
    # lastModified = 'Sun, 16 Nov 2025 16:30:50 GMT'
    # lastMention = _parse_date(lastModified)
    while not stop:
        try:
            rss = parse(RSS_URL, etag=etag, modified=prevRssMod)
            status = rss['status']
            if (status == 304):
                await asyncio.sleep(SLEEP)
                continue
            if (status != 200):
                raise RuntimeError(f"Can't connect to '{RSS_URL}'.")

            etag = rss['etag']
            prevRssMod = rss['feed']['updated']
            entries: list = rss['entries']
            entries.sort(key=lambda entry: entry['published_parsed'], reverse=True)

            for entry in entries:
                if (entry['published_parsed'] <= lastMention):
                    break
                mention = entry['title'].split(' mentioned @')
                print('[DEBUG] entry: ', entry, flush=True)
                if (mention[1] == ctx['user'] or ctx['user'] == '*'):
                    if (not ctx['cli']):
                        await sendNotif(entry['title'], entry['summary'], entry['link'], ctx['user'] == '*')
                    else:
                        sendNotifCli(entry['title'], entry['summary'], entry['link'], ctx['user'] == '*')

            strLastMention = entries[0]['published']
            lastMention = entries[0]['published_parsed'] # Publish time of most recent mention
            updateMention(ctx['config'], strLastMention)
            await asyncio.sleep(SLEEP)
            # if i == 1:
            #     RSS_URL = open('rss-2.xml').read()
            #     i = 2
            # if i == 2:
            #     RSS_URL = open('rss-3.xml').read()
            #     i = 3
            # elif i == 3:
            #     RSS_URL = open('rss-4.xml').read()
            #     stop = True
        except CancelledError as e: # Ctrl+C
            stop = True

def main():
    import os, asyncio, requests

    args = parseArgs()

    if (args.config == None):
        config = DEFAULT_CONFIG_PATH
    else:
        config = args.config

    if (args.init or not os.path.isfile(config)):
        _init({'config': args.config, 'user': args.user, 'subs': args.subscribe_to})

    if (args.no_config):
        conf = {}
    else:
        conf = getConfig(config)

    if (args.user != None):
        conf['User'] = args.user
    if (args.subscribe_to != None):
        conf['Subscribe'] = args.subscribe_to

    if ('LastMention' in conf and conf['LastMention'] != 'None' and not _isEmptyOrSpace(conf['LastMention'])):
        lastMention = conf['LastMention']
    else:
        # Note:
        # With the RSS bug we found that is only showing messages 1 step behind this will now make a bug
        # Where the first time you run `dr-mentiond` you won't see the last few messages, but this bug is acceptable
        # to me in the grand scheme of things. A few messages missed as a one time thing when you install the script
        # is nothing
        resp = requests.head(RSS_URL)
        if (resp.status_code != 200):
            raise RuntimeError(f"Can't connect to '{RSS_URL}'.")
        lastMention = resp.headers['Last-Modified']
        updateMention(config, lastMention)
    
    ctx = {
        'config': config,
        'user': conf['User'],
        'lastMention': lastMention,
        'subs': conf['Subscribe'],
        'cli': args.cli
    }
    asyncio.run(rss_listen(ctx))

def parseArgs():
    from argparse import ArgumentParser

    parser = ArgumentParser(
        prog='dr-mentiond',
        description='Sends desktop notifications about devRant mentions and rants.',
    )
    parser.add_argument('--init', action='store_true', help="Initialize a new config file.")
    parser.add_argument('-c', '--config', help=f'Specify a config file, (default is {DEFAULT_CONFIG_PATH}). " \
        "Mutually exclusive with --no-config.')
    parser.add_argument('-n', '--no-config', action='store_true', help=
        "Ignore the config file and take information about user and subscribes from --user and --subscribe-to. ' \
        'Option --user must be supplied if this flag is enabled. Mutually exclusive with --config.")
    parser.add_argument('-u', '--user', help=f"Override the config file's 'User=' setting.")
    parser.add_argument('-s', '--subscribe-to', action='append' , help=
        "Override to the config file's 'Subscribe=' setting. " \
        "Specify --subscribe-to for each ranter you want to subscribe to")
    parser.add_argument('-t', '--cli', action='store_true', help="Run the script in cli mode. " \
        "Print notifications to the terminal(stdout) instead of as desktop notifications.")

    args = parser.parse_args()
    
    if (args.no_config and args.config != None):
        parser.error("Options --no-config and --config are mutually exclusive!")
    if (args.no_config and args.user == None):
        parser.error("When --no-config flag is specified, --user option is required!")

    return args

def _init(ctx):
    from sys import stderr
    try:
        print('Initializing a new config profile:')

        if (ctx['config'] == None):
            confPath = input(f'Enter config file for the profile ({DEFAULT_CONFIG_PATH}): ').strip()
            if _isEmptyOrSpace(confPath):
                confPath = DEFAULT_CONFIG_PATH
        else:
            confPath = ctx['config']
            print(f'Enter config file for the profile ({DEFAULT_CONFIG_PATH}): {confPath}')
        
        if (ctx['user'] == None):
            user = None
            while _isEmptyOrSpace(user):
                user = input('Enter your devRant nick: @')
        else:
            user = ctx['user']
            print(f'Enter your devRant nick: @{user}')

        print('Enter a list of users whoose rants you want to follow and get notified of: (you can change this list at any time)')
        print("(To stop, press 'Enter' without typing anything)")
        if (ctx['subs'] == None):
            subs = []
            sub = input('Subscribe to @')
            while not _isEmptyOrSpace(sub):
                subs.append(sub)
                sub = input('Subscribe to @')
        else:
            subs = ctx['subs']
            for sub in subs:
                print(f'Subscribe to @{sub}')

        print()
        print(f"The following will be saved into '{confPath}':")
        print('User=' + user)
        for sub in subs:
            print('Subscribe=' + sub)
        question = input('Is this okay? (Y/n) ').lower()
        if (_isEmptyOrSpace(question) or question == 'y' or question == 'yes'):
            print(f"Saving...")
            try:
                initConfig(confPath, user, subs)
            except Exception as ex:
                print(f"Failed to save configuration file: " + str(ex), file=stderr, flush=True)
                exit(1)
            print(f"Configuration saved to '{confPath}'.")
    except KeyboardInterrupt:
        print(" Recieved Ctrl+C. Cancelling...")
        exit(1)
    exit(0)

if (__name__ == "__main__"):
    main()
