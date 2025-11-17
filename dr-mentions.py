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
SLEEP = 15

notifier = DesktopNotifier('devRant Mentions', Icon(uri=ICON_PATH))

async def sendNotif(author: str, summary: str, link: str):
    from webbrowser import open
    await notifier.send(
        title=author + ' mentioned you in a comment!',
        message=summary.replace('&quot;', '"') + "\n" + link,
        buttons=[Button("Open in Browswer", lambda: open(link))],
        on_clicked=lambda: open(link)
    )

def sendNotifCli(author: str, summary: str, link: str):
    header = f' 🔴 {author} mentioned you in a comment!    '
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
    lastModified: str = ctx['lastModified']
    lastMention = _parse_date(lastModified)
    stop: bool = False

    # i = 1
    # RSS_URL = open('rss-1.xml').read()
    # lastModified = 'Sun, 16 Nov 2025 16:30:50 GMT'
    # lastMention = _parse_date(lastModified)
    while not stop:
        try:
            rss = parse(RSS_URL, etag=etag, modified=lastModified)
            status = rss['status']
            if (status == 304):
                await asyncio.sleep(SLEEP)
                continue
            if (status != 200):
                raise RuntimeError(f"Can't connect to '{RSS_URL}'.")

            etag = rss['etag']
            lastModified = rss['feed']['updated']
            entries: list = rss['entries']
            entries.sort(key=lambda entry: entry['published_parsed'], reverse=True)

            for entry in entries:
                if (entry['published_parsed'] < lastMention):
                    break
                mention = entry['title'].split(' mentioned @')
                if (mention[1] == ctx['user']):
                    if (not ctx['cli']):
                        await sendNotif(mention[0], entry['summary'], entry['link'])
                    else:
                        sendNotifCli(mention[0], entry['summary'], entry['link'])

            lastMention = rss['feed']['updated_parsed']
            updateMention(ctx['config'], lastModified)
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
        lastModified = conf['LastMention']
    else:
        resp = requests.head(RSS_URL)
        if (resp.status_code != 200):
            raise RuntimeError(f"Can't connect to '{RSS_URL}'.")
        lastModified = resp.headers['Last-Modified']
        updateMention(config, lastModified)
    
    ctx = {
        'config': config,
        'user': conf['User'],
        'lastModified': lastModified,
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

async def test():
    import asyncio
    messages = [{
        'author': 'retoor',
        'link': 'https://devrant.com/rants/19381730',
        'message': '''@SoldierOfCode https://devrant.com/rants/19384567/...'''
    },{
        'author': 'retoor',
        'link': 'https://devrant.com/rants/19384567',
        'message': '''@SoldierOfCode and @Lensflare

    Edit: @Lensflare structure is totally the same, guuid has a different format tho. 

    @SoldierOfCode your @whimsical @whimsical @whimsical @whimsical test still shows as one mention, because it works per unique name. So mention to two different users will do result in seperate items.
                            '''
    },{
        'author': 'retoor',
        'link': 'https://devrant.com/rants/19384567',
        'message': '''@SoldierOfCode and @Lensflare

    Edit: @Lensflare structure is totally the same, guuid has a different format tho. 

    @SoldierOfCode your @whimsical @whimsical @whimsical @whimsical test still shows as one mention, because it works per unique name. So mention to two different users will do result in seperate items.
                            '''
    },{
        'author': 'retoor',
        'link': 'https://devrant.com/rants/19384567',
        'message': '''@SoldierOfCode and @Lensflare

    Edit: @Lensflare structure is totally the same, guuid has a different format tho. 

    @SoldierOfCode your @whimsical @whimsical @whimsical @whimsical test still shows as one mention, because it works per unique name. So mention to two different users will do result in seperate items.
                            '''
    },{
        'author': 'CoreFusionX',
        'link': 'https://devrant.com/rants/19384359',
        'message': '''@CaptainRant 

    If you quit your job and want to start in a new stack from scratch, you go back to being a junior, and that's it. Your previous knowledge should allow you to climb relatively fast, but you are still a junior in the stack.
                            '''
    },{
        'author': 'whimsical',
        'link': 'https://devrant.com/rants/19381730',
        'message': '''@SoldierOfCode ah, makes it a bit more complex, but thanks for your research. I gonna eat and will fix it and thanks for the test data 😁 also, I'm never bored :p I see you guys as top priority 😁 after snek users :p
                            '''
    },{
        'author': 'whimsical',
        'link': 'https://devrant.com/rants/19384456',
        'message': '''@Lensflare he doesn't have the balls :p
                            '''
    },{
        'author': 'Lensflare',
        'link': 'https://devrant.com/rants/19384456',
        'message': '''@whimsical why would you give him ideas like this?
    Now he will flood it with pictures of his dick and his literal shit.
    And you are warning HIM of the content there?
                            '''
    },{
        'author': 'SoldierOfCode',
        'link': 'https://devrant.com/rants/19381730',
        'message': '''For example, this test message should generate four mentions: @whimsical @whimsical @whimsical @whimsical

    ('should' as in, I suspect it will, correctly it should only generate one)
                            '''
    },{
        'author': 'SoldierOfCode',
        'link': 'https://devrant.com/rants/19381730',
        'message': '''@whimsical OHHH, I looked at the XML and THAT'S why there are &quot;duplicates&quot;! The XML file actually DOES show three different items for your message, one for &quot;whimsical mentioned(at)SoldierOfCode&quot; and two(because you mentioned him twice) for (at)Lensflare, but since all three have the same guid the RSS software sees them as one. That's probably the &quot;duplicates&quot; @Lensflare was seeing, in which case it's not duplicates and it works.

    Tho you should probablt treat the case where you mention the person more than once in the same message so it'd only generate one item per person.

    And for the guid's you could make it instead of `devrant-mention-19384527` be `devrant-mention-19384527-1` for example, and for each additional mention ++ the counter so second mention(in the same message) would be `devrant-mention-19384527-2` and continued
                            '''
    },{
        'author': 'SoldierOfCode',
        'link': 'https://devrant.com/rants/19381730',
        'message': '''@whimsical OHHH, I looked at the XML and THAT'S why there are &quot;duplicates&quot;! The XML file actually DOES show three different items for your message, one for &quot;whimsical mentioned(at)SoldierOfCode&quot; and two(because you mentioned him twice) for (at)Lensflare, but since all three have the same guid the RSS software sees them as one. That's probably the &quot;duplicates&quot; @Lensflare was seeing, in which case it's not duplicates and it works.

    Tho you should probablt treat the case where you mention the person more than once in the same message so it'd only generate one item per person.

    And for the guid's you could make it instead of `devrant-mention-19384527` be `devrant-mention-19384527-1` for example, and for each additional mention ++ the counter so second mention(in the same message) would be `devrant-mention-19384527-2` and continued
                            '''
    },{
        'author': 'SoldierOfCode',
        'link': 'https://devrant.com/rants/19381730',
        'message': '''@whimsical Oh, btw, I just noticed the RSS feed only reports one mention. For example your messgse here was reported as &quot;whimsical mentioned (at)SoldierOfCode&quot; but does report that you also mentioned (at)Lensflare
                            '''
    },{
        'author': 'whimsical',
        'link': 'https://devrant.com/rants/19381730',
        'message': '''@SoldierOfCode aww, thanks. I will look in it today, duplication also mentioned by @Lensflare. But I don't know if I can add the &quot;Add new rant&quot; notifs in this rss because it maybe breaks @Lensflare system that depends on it. Maybe I could make extra rss. Will see how far I get :)
                            '''
    },{
        'author': 'whimsical',
        'link': 'https://devrant.com/rants/19381730',
        'message': '''@SoldierOfCode aww, thanks. I will look in it today, duplication also mentioned by @Lensflare. But I don't know if I can add the &quot;Add new rant&quot; notifs in this rss because it maybe breaks @Lensflare system that depends on it. Maybe I could make extra rss. Will see how far I get :)
                            '''
    },{
        'author': 'D-4got10-01',
        'link': 'https://devrant.com/rants/19384402',
        'message': '''@whimsical I wouldn't be surprised if it was either malicious or a marketing move... or both.

    'Want to know whether this paper has been written by a human or is machine-generated? _We_ have a solution for you. Subscribe.',
                            '''
    },{
        'author': 'whimsical',
        'link': 'https://devrant.com/rants/19384402',
        'message': '''@D-4got10-01 yeah, you could think maybe, leave it there just like pictures from gemini have a little logo so you can see it's AI.
                            '''
    },{
        'author': 'AlgoRythm',
        'link': 'https://devrant.com/rants/19384200',
        'message': '''@Lensflare I don't quite see myself working with Swift or Kotlin in the foreseeable future, unfortunately. I do quite like Swift though, maybe I'll spend a weekend with it one of these times.
                            '''
    },{
        'author': 'AlgoRythm',
        'link': 'https://devrant.com/rants/19384200',
        'message': '''@Lensflare That's the tragedy, isn't it? Excited to learn it, but crushed by the reality that it'll only ever benefit me in personal projects or academically.
                            '''
    }
    ]
    
    messages.append(messages[10])
    for msg in messages[-3:]:
        await sendNotif(msg['author'], msg['message'], msg['link'])
    
    await asyncio.sleep(5)

if (__name__ == "__main__"):
    main()
    # import asyncio
    # asyncio.run(test())