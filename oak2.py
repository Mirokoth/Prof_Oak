# modules
import asyncio
import sys
import os
import json
import re

# third-party modules
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import discord
import requests
from bs4 import BeautifulSoup
from discord import role
import pyowm

# config
import config

# define paths
DIRECTORY = os.path.dirname(os.path.abspath(__file__)) # relative directory
PATH_GAUTH = DIRECTORY + config.GAUTH
PATH_IMG_OAK = DIRECTORY + '/images/Oak1.png'
PATH_IMG_NERD = DIRECTORY + '/images/nerd.jpg'
PATH_POKEMON_DB = DIRECTORY + config.POKEMON_DB
with open(DIRECTORY + config.HELP_FILE) as HELP:
    PATH_HELP_TEXT = HELP
OWM_TOKEN = config.OWM_TOKEN
ADMINS = json.load(open(DIRECTORY + '/data/admins.json'))['admins']

client = discord.Client()
_roles = []

# Check if the user is an admin
def isAdmin(serverId, userId):
    # Check admins list
    for adminId in ADMINS:
        if adminId == userId:
            return True
    # Check owner
    ownerId = client.get_server(serverId).owner.id
    if ownerId == userId:
        return True
    return False

# Bot Ready
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    print('Connected servers...')
    print('------')
    for server in client.servers:
        print(server.name + ' (' + server.id + ')')
        print('------')
    print('Roles')
    print('------')
    for role in server.roles:
        _roles.append(role)
        print(role.name + ' (' + role.id + ')')
    print('------')
    print('Prof Oak ready to party')
    print('------')

# New Member Joins
@client.event
async def on_member_join(member):
    print("new user: {} ({})".format(member.name, member.id))
    await client.send_message(member.server, 'Welcome <@{}>!'.format(member.id))
    await client.send_message(member, 'Welcome <@{}>!\n\nType **!help** to get started!'.format(member.id))

# Message Received
@client.event
async def on_message(message):

    # Command: Help pm
    if message.content.upper().startswith('!HELP'):
        _help = '**Assigning team:**\n!role teamname or !role teamcolour\n\n**Finding a Pokemon:**\n!find Pokemon_Name\n\n**Updating database of pokemon locations:**\n!c or !caught or !found\nfor a single pokemon just enter its name\nfor multiple pokemon put them in square brackets [ ]\nfollow it with the location.\n\nFor expample:\n!Found [Pikachu Squirtle Zubat] Valhalla\nor\n!c Pikachu Charnwood\n\n**Server status:**\n!status\n\n**Current Canberra Temperature:**\n!temp\n\nMore to come! If you have any feature requests message @Mirokoth'
        await client.send_message(message.channel, ':envelope:')
        await client.send_message(message.author, '{}'.format(_help))

    #Commadn: Help channel
    if message.content.upper().startswith('!HELP US'):
        _help = '**Assigning team:**\n!role teamname or !role teamcolour\n\n**Finding a Pokemon:**\n!find Pokemon_Name\n\n**Updating database of pokemon locations:**\n!c or !caught or !found\nfor a single pokemon just enter its name\nfor multiple pokemon put them in square brackets [ ]\nfollow it with the location.\n\nFor expample:\n!Found [Pikachu Squirtle Zubat] Valhalla\nor\n!c Pikachu Charnwood\n\n**Server status:**\n!status\n\n**Current Canberra Temperature:**\n!temp\n\nMore to come! If you have any feature requests message @Mirokoth'
        await client.send_message(message.channel, '{}'.format(_help))

    # Command: Find pokemon
    if message.content.upper().startswith('!FIND'):

            # Search publically (in summoned channel)
            if '!find us' in message.content:
                _term = message.content.replace('!find us ', '')
                _term = _term.title()
                _sendTo = message.channel
            # Search privately (direct message)
            else:
                _term = message.content.replace('!find ', '').title()
                _term = _term.title()
                _sendTo = message.author

            # Send notification
            tmp = await client.send_message(_sendTo, 'Searching...\n')

            # Easter eggs
            if 'OAK' in _term.upper():
                await client.send_file(message.channel, PATH_IMG_OAK)
            if 'MIRO' in _term.upper() or 'KOSTA' in _term.upper():
                await client.send_file(message.channel, PATH_IMG_NERD)

            # Search PATH_POKEMON_DB .json file for pokemon
            with open(PATH_POKEMON_DB) as _poke_db:
                _pokemon = json.load(_poke_db)
            try:
                _pokemon = _pokemon[_term]
            except KeyError as e:
                await client.edit_message(tmp, 'Sorry but we could not find {}. \nPlease confirm name'.format(_term))
            location = ''
            if type(_pokemon['location']) is not str:
                for local in _pokemon['location']:
                    location += local
                    location += '\n'
            if type(_pokemon['location']) is str:
                location += _pokemon['location']

            # Send result
            await client.edit_message(tmp, '**{}** found at the following location(s):\n```\n{}```\nAnd can be obtained by:\n```\n{}\n```'.format(_term, location, _pokemon['alternative']))

            # Let console know what is going on
            print('{} Is wasting your bandwidth, Searching for {}'.format(message.author, _term))

    # Command: Add new locations to pokemon database
    if message.content.upper().startswith('!C') or message.content.upper().startswith('!CAUGHT') or message.content.upper().startswith('!FOUND'):
        print('Updating pokemon Database - Requested by {}'.format(message.author))
        _prnt = await client.send_message(message.channel, 'Adding...')
        regex = '.*?\[(.*?)\].*?'
        if '[' in message.content:
            _poke_edit = re.match(regex, message.content).group(1).split(' ')
            _locations = message.content.split('] ')[1]
            _singlemon = False
        else:
            _poke_edit = message.content.split(' ')
            _locations = ' '.join(_poke_edit[2:]).title()
            _poke_edit = _poke_edit[1]
            _singlemon = True

        with open(PATH_POKEMON_DB, 'r') as _poke_db:
            _pokemon = json.load(_poke_db)

        if _singlemon == True:
            _currentloop = False
            try:
                _pokemon_ed = _pokemon[_poke_edit.title()]
            except KeyError as e:
                await client.send_message(message.channel, '{} not found, please confirm spelling'.format(_poke_edit))
                _currentloop = True
            if _currentloop == False:
                if type(_pokemon_ed['location']) is not str:
                    _pokemon_ed['location'].append(_locations)
                if type(_pokemon_ed['location']) is str:
                    _tempLst = []
                    _tempLst.append(_pokemon_ed['location'])
                    _pokemon_ed['location'] = _tempLst
                    _pokemon_ed['location'].append(_locations)
                with open(PATH_POKEMON_DB, 'w') as _poke_db:
                    json.dump(_pokemon, _poke_db)
                    _poke_db.close()
                    await client.edit_message(_prnt, 'Added {} to {}'.format(_locations,_poke_edit))
            else:
                pass

        if _singlemon == False:
            _notfound = ''
            _found = ''
            _was_not_found = False
            for poke in _poke_edit:
                _currentloop = False
                try:
                    _pokemon_ed = _pokemon[poke.title()]
                    _found += "{} ".format(poke)
                except KeyError as e:
                    _notfound += "{} ".format(poke)
                    _was_not_found = True
                    _currentloop = True
                if _currentloop == False:
                    if type(_pokemon_ed['location']) is not str:
                        _pokemon_ed['location'].append(_locations)
                    if type(_pokemon_ed['location']) is str:
                        _tempLst = []
                        _tempLst.append(_pokemon_ed['location'])
                        _pokemon_ed['location'] = _tempLst
                        _pokemon_ed['location'].append(_locations)
                    with open(PATH_POKEMON_DB, 'w') as _poke_db:
                        json.dump(_pokemon, _poke_db)
                        _poke_db.close()
                else:
                    pass
            if _was_not_found == True:
                await client.edit_message(_prnt, 'Added {} to {} but was unable to add {}'.format(_locations,_found,_notfound))
            if _was_not_found == False:
                await client.edit_message(_prnt, 'Added {} to {}'.format(_locations,_found))

    # Command: Get a role ID form a role mention
    if message.content.upper().startswith('!ROLEID'):
        # grab first role mentioned
        firstRole = message.role_mentions[0]
        if firstRole:
            await client.send_message(message.channel, "Role '" + firstRole.name + "' ID: " + firstRole.id)

    # Command: Get Pokemon Go server status
    if message.content.upper().startswith('!STATUS'):
            stat_msg = await client.send_message(message.channel, 'This can sometimes take a while...')

            try:
                _page = requests.get(
                            'http://www.mmoserverstatus.com/pokemon_go',
                            timeout=120)
            except TimeOut as e:
                # Error handling: on site timeout advise server is most likely down
                await client.send_message(message.channel, 'Site did not respond in time, server is most likely down.')
            _page.text
            _page_cont = _page.content
            _soup_page = BeautifulSoup(_page_cont, "html.parser")
            _soup_li = _soup_page.find_all("li", "white")
            if 'fa fa-check' in str(_soup_li[0]):
                await client.edit_message(stat_msg, 'Australian server: ONLINE ')
                print("Running a P:GO server check - Server up")
            else:
                await client.send_message(message.channel, 'Australian server: OFFLINE ')
                print('server offline')

    # Command: Get Canberra weather
    if message.content.upper().startswith('!TEMP'):
        tmpw = await client.send_message(message.channel, 'Incredibly Inaccurate weather reading')
        """ Weather Details"""
        owm = pyowm.OWM(OWM_TOKEN)
        _weather_location = owm.weather_at_place('Canberra,AU')
        _observation = _weather_location.get_weather()
        _observation = _observation.get_temperature('celsius')
        await client.edit_message(tmpw, 'It is currently {}°C'.format(_observation['temp']))

    # Command: Assign team
    if message.content.upper().startswith('!ROLE'):
        _term = message.content.split(' ')
        _tmp_count = 0

        for role in message.author.roles:
            if 'Mystic' in role.name:
                _tmp_count =+ 1
            elif 'Valor' in role.name:
                _tmp_count =+ 1
            elif 'Instinct' in role.name:
                _tmp_count =+ 1

        if 'ADMIN' in _term[1].upper():
            await client.send_message(message.channel, 'http://i.imgur.com/MqxSRTm.jpg')
            _tmp_count =+ 5

        if _tmp_count == 0:
            if 'MY' in _term[1].upper() or 'BL' in _term[1].upper():
                for role in _roles:
                    if 'MYSTIC' in str(role.name.upper()) and 'ADMIN' not in str(role.name.upper()):
                        await client.add_roles(message.author, role)
                        await client.send_message(message.channel, 'Welcome to team {}!'.format(role.name))
            if 'VA' in _term[1].upper() or 'RE' in _term[1].upper():
                for role in _roles:
                    if 'VALOR' in str(role.name.upper()) and 'ADMIN' not in str(role.name.upper()):
                        await client.add_roles(message.author, role)
                        await client.send_message(message.channel, 'Welcome to team {}!'.format(role.name))
            if 'IN' in _term[1].upper() or 'YE' in _term[1].upper():
                for role in _roles:
                    if 'INSTINCT' in str(role.name.upper()) and 'ADMIN' not in str(role.name.upper()):
                        await client.add_roles(message.author, role)
                        await client.send_message(message.channel, 'Welcome to team {}!'.format(role.name))
        if _tmp_count >= 5:
            await client.send_message(message.channel, 'Nice try ;)')
        else:
            await client.send_message(message.channel, 'It looks like you already have a team.\nIf you think this is an error please let us know')

    if message.content.upper().startswith('!SING'):
        theme = ['I', 'want', 'to', 'be', 'the', 'very', 'best', 'like', 'no', 'one', 'ever', 'was', ':blush:']
        sing = await client.send_message(message.channel, '*clears throat*')
        for lyric in theme:
            await client.edit_message(sing, lyric)

    # Command: Restart server
    if message.content.upper().startswith('!RESTART'):
        # Authorise command
        if isAdmin(message.server.id, message.author.id):
            await client.send_message(message.channel, '<@{}> is pushing my buttons..'.format(message.author.id))
            os.execv(sys.executable, ['python3'] + sys.argv)

    #Commadn: Kill server
    if message.content.upper().startswith('!DIE'):
        quit()

# Start Discord client
client.run(config.BOT_TOKEN)
