# modules
import asyncio
import sys
import os
import json

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
PATH_IMG_OAK = DIRECTORY + '\\images\\Oak1.png'
PATH_IMG_NERD = DIRECTORY + '\\images\\nerd.jpg'
PATH_POKEMON_DB = DIRECTORY + config.POKEMON_DB
PATH_HELP_TEXT = DIRECTORY + config.HELP_FILE

client = discord.Client()
_roles = []

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

# New Member Joins
@client.event
async def on_member_join(member):
    print("new user: {}".format(member))
    _user = str(member).split('#')
    _user = _user[0]
    await client.send_message(member.server, 'Welcome {}'.format(_user))
    await client.send_message(member, 'Welcome {}!\nTo get started type **!help**'.format(_user))

# Message Received
@client.event
async def on_message(message):

    # Command: Help
    if message.content.startswith('!help'):
        _help = '**Assigning team:**\n!role teamname or !role teamcolour\n\n**Finding a Pokemon:**\n!find Pokemon_Name\n\n**Server status:**\n!status\n\n**Current Canberra Temperature:**\n!temp\n\nMore to come! If you have any feature requests message @Mirokoth'
        await client.send_message(message.channel, '{}'.format(_help))

    # Command: Find pokemon
    if message.content.startswith('!find'):

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
            if 'Oak' in _term:
                await client.send_file(message.channel, PATH_IMG_OAK)
            if 'MIRO' in _term.upper() or 'KOSTA' in _term.upper():
                await client.send_file(message.channel, PATH_IMG_NERD)

            # Get Google Sheet from API
            scope = ['https://spreadsheets.google.com/feeds']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(PATH_GAUTH, scope)
            gc = gspread.authorize(credentials)
            sheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1xGH7HNNZvrOlAd1U1RogF4hlMlmN-gSFbeBpZ0gpnBY/edit#gid=0')
            worksheet = sheet.get_worksheet(0)

            # Search Google Sheet for pokemon
            try:
                _result = worksheet.find(_term)
            except gspread.exceptions.CellNotFound as e:
                await client.send_message(message.channel, 'Sorry but we could not find {}. Please confirm name'.format(_term))

            _output = worksheet.cell(_result.row, _result.col+1).value
            _output = _output.replace(',', '\n')
            print('Someone searched for {}'.format(_term))

            # Send result
            await client.edit_message(tmp, '**{}** found at the following location(s):\n```\n {} \n```'.format(_term, _output.strip()))

    # Command: Get a role ID from a role mention
    if message.content.startswith('!roleid'):
        # Grab first role mentioned
        firstRole = message.role_mentions[0]
        if firstRole:
            await client.send_message(message.channel, "Role '" + firstRole.name + "' ID: " + firstRole.id)

    # Command: Get Pokemon Go server status
    if message.content.startswith('!status'):
            await client.send_message(message.channel, 'This can sometimes take a while...')

            _page = requests.get(
                            'http://www.mmoserverstatus.com/pokemon_go',
                            timeout=120)
            _page.text
            _page_cont = _page.content
            _soup_page = BeautifulSoup(_page_cont, "html.parser")
            _soup_li = _soup_page.find_all("li", "white")
            if 'fa fa-check' in str(_soup_li[0]):
                await client.send_message(message.channel, 'Australian server: ONLINE ')
                print("Running a server check - Server up")
            else:
                await client.send_message(message.channel, 'Australian server: OFFLINE ')
                print('server offline')

    # Command: Get Canberra weather
    if message.content.startswith('!temp'):
        """ Weather Details"""
        owm = pyowm.OWM('c70f0e635539159ab87dc1b61f812d5d')
        _weather_location = owm.weather_at_place('Canberra,AU')
        _observation = _weather_location.get_weather()
        _observation = _observation.get_temperature('celsius')
        await client.send_message(message.channel, 'It is currently {}°C'.format(_observation['temp']))

    # Command: Assign team
    if message.content.startswith('!role'):
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

    # Command: Kill server
    if message.content.startswith('!die'):
        await quit()

# Start Discord client
client.run(config.BOT_TOKEN)
