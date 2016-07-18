# modules
import asyncio
import sys
import os
import json
import re
from time import strftime
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
BOT_CMD_SYMBOL = config.BOT_CMD_SYMBOL
COMMAND_LOG = DIRECTORY + config.COMMAND_LOG

client = discord.Client()
roles = []

# --------------
# Helper Methods
# --------------

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

# Check if message is a command
def isCmd(message):
    if len(message) > 0 and message[0] == BOT_CMD_SYMBOL:
        return True
    return False

# Logs all user command inputs to COMMAND_LOG
def command_log(author, author_id, command):
    with open(COMMAND_LOG, 'a') as log_output:
        #Appends Time and date - User and UserID - Command ran
        log_output.write('n' + '{}  -  {} ({}) used the following command: {}'.format(strftime('%H:%M - %d-%b-%Y'), author, author_id, command))
        log_output.close()
    print('Updated command log')

# Clean input
def sanitiseCmd(message):
    # Remove white space sequences
    message = ' '.join(message.split())
    # Grab words
    words = message.split(' ')
    return words

# Get command
def getCmd(message):
    words = sanitiseCmd(message)
    # Extract command
    command = words[0][1:].upper()
    return command

# Get arguments
def getArgs(message):
    words = sanitiseCmd(message)
    # Extract arguments
    arguments = words[1:]
    if len(arguments) == 0:
        return False
    return arguments

# --------------
# Event Handlers
# --------------

# Bot Ready
@client.event
async def on_ready():
    print('Logged in as {} ({}) with the following connected servers..'.format(client.user.name, client.user.id))
    print('------')
    for server in client.servers:
        print('{} ({})'.format(server.name, server.id))
        print('------')
    # Cache server roles
    print('Roles')
    print('------')
    for role in server.roles:
        roles.append(role)
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

    # Check if message is a command
    if isCmd(message.content):
        # Log command to console
        command = getCmd(message.content)
        arguments = getArgs(message.content)
        print("{} ({}) used the following command: {}".format(message.author.name, message.author.id, command))
        # Send message of to be Logged
        command_log(message.author.name, message.author.id, message.content)
    else:
        return

    # Command: Help
    if command == "HELP":

        helpMsg = '**Assigning team:**\n!role teamname or !role teamcolour\n\n**Finding a Pokemon:**\n!find Pokemon_Name\n\n**Updating database of pokemon locations:**\n!c or !caught or !found\nfor a single pokemon just enter its name\nfor multiple pokemon put them in square brackets [ ]\nfollow it with the location.\n\nFor expample:\n!Found [Pikachu Squirtle Zubat] Valhalla\nor\n!c Pikachu Charnwood\n\n**Location Search:**\nFind what pokemon can be found in an area by entering:\n!location **area**\n\n**Server status:**\n!status\n\n**Current Canberra Temperature:**\n!temp\n\nMore to come! If you have any feature requests message @Mirokoth'

        # Public
        if arguments and arguments[0].upper() == "US":
            sendTo = message.channel
        # Private
        else:
            sendTo = message.author
            await client.send_message(message.channel, 'Check your mailbox kiddo! :incoming_envelope:')
        await client.send_message(sendTo, '{}'.format(helpMsg))

    # Command: Find pokemon
    if command == "FIND":

            # No arguments
            if not arguments:
                await client.send_message(message.channel, "Please specify a pokemon, e.g. {}find zubat".format(BOT_CMD_SYMBOL))
            # Search publically (in summoned channel)
            elif arguments and arguments[0].upper() == "US":
                sendTo = message.channel
                pokemon = arguments[1].title()
            # Search privately (direct message)
            else:
                sendTo = message.author
                pokemon = arguments[0].title()
                await client.send_message(message.channel, 'Check your mailbox kiddo! :incoming_envelope:')

            # Send 'searching..' notification
            tmp_msg = await client.send_message(sendTo, 'Looking for **{}**..'.format(pokemon))

            # Easter eggs
            if 'OAK' in pokemon.upper():
                await client.send_file(message.channel, PATH_IMG_OAK)
            if 'MIRO' in pokemon.upper() or 'KOSTA' in pokemon.upper():
                await client.send_file(message.channel, PATH_IMG_NERD)

            # Search local data store for pokemon
            with open(PATH_POKEMON_DB) as poke_db:
                pokemons = json.load(poke_db)
            # Find pokemon in data store
            try:
                pokemons = pokemons[pokemon]
            except KeyError as e:
                pokemons = False
                await client.edit_message(tmp_msg, "Sorry, I couldn't find that pokemon pal!".format(pokemon))

            # Pokemon is found
            if pokemons:
                location = ''
                # Multiple existing locations in an array
                # NOTE: This should be replaced so that they're always in an array
                if type(pokemons['location']) is not str:
                    for loc in pokemons['location']:
                        location += loc
                        location += '\n'
                # Single existing location
                if type(pokemons['location']) is str:
                    location += pokemons['location']
                # Send result
                # Alt field not empty
                if pokemons['alternative'] != "":
                    await client.edit_message(tmp_msg, '**{}** found at the following location(s):\n```\n{}```\nAnd can be obtained by:\n```\n{}\n```'.format(pokemon, location, pokemons['alternative']))
                # Alt field empty
                else:
                    await client.edit_message(tmp_msg, '**{}** found at the following location(s):\n```\n{}```'.format(pokemon, location))
            else:
                print("No pokemons")

            # Let console know what is going on
            print('{} is wasting your bandwidth by searching for {}'.format(message.author, pokemon))

    # Command: Add new location to pokemon database
    # NOTE: Need to check if the location already exists
    if command == "C" or command == "CAUGHT" or command == "FOUND":

        print('{} is attempting to update the pokemon database..'.format(message.author))
        # Send 'searching..' notification
        tmp_msg = await client.send_message(message.channel, 'One sec..')

        regex = '.*?\[(.*?)\].*?'
        single = True

        # Multiple pokemon separated ie. [poke1 poke2]
        if '[' in message.content:
            pokemon = re.match(regex, message.content).group(1).split(' ')
            location = message.content.split('] ')[1]
            single = False
        # Single pokemon
        else:
            pokemon = message.content.split(' ')
            location = ' '.join(pokemon[2:]).title()
            pokemon = [ pokemon[1] ]

        # Read local data store for pokemon
        with open(PATH_POKEMON_DB, 'r') as poke_db:
            pokemonJson = json.load(poke_db)

        found = []
        not_found = []
        for poke in pokemon:
            valid = True
            # Pokemon is valid
            try:
                pokemon = pokemonJson[poke.title()]
                found.append(poke)
            # Pokemon is NOT valid
            except KeyError as e:
                valid = False
                not_found.append(poke)
            # When valid
            if valid == True:
                # Multiple existing locations in an array
                # NOTE: This should be replaced so that they're always in an array
                if type(pokemon['location']) is not str:
                    pokemon['location'].append(location)
                # Single existing location
                if type(pokemon['location']) is str:
                    _tempLst = []
                    _tempLst.append(pokemon['location'])
                    pokemon['location'] = _tempLst
                    pokemon['location'].append(location)
                # Write to local data store
                with open(PATH_POKEMON_DB, 'w') as poke_db:
                    json.dump(pokemonJson, poke_db)
                    poke_db.close()
            # When invalid
            else:
                pass

        # All pokemon were NOT found
        if len(found) == 0 and len(not_found) > 0:
            if single == True:
                await client.edit_message(tmp_msg, "That doesn't sound like a pokemon, e.g. **{}found zubat cave**".format(BOT_CMD_SYMBOL))
            else:
                await client.edit_message(tmp_msg, "They don't sound like pokemon, e.g. **{}found [zubat golbat] cave**".format(BOT_CMD_SYMBOL))
        # Pokemon were BOTH found and not found
        elif len(found) > 0 and len(not_found) > 0:
            found = ", ".join(found).title()
            not_found = ", ".join(not_found).title()
            await client.edit_message(tmp_msg, "I've added **{}** to the locadex for **{}**, but **{}** don't sound like pokemon!".format(location, found, not_found))
        # Pokemon were ONLY FOUND
        elif len(found) > 0 and len(not_found) == 0:
            found = ", ".join(found).title()
            await client.edit_message(tmp_msg, "Good find kiddo. **{}** has been added to the locadex for **{}**!".format(location, found))
        # Pokemon were ONLY NOT FOUND
        elif len(found) == 0 and len(not_found) > 0:
            not_found = ", ".join(not_found).title()
            await client.edit_message(tmp_msg, "That doesn't sound like a pokemon, e.g. **{}found zubat cave**".format(BOT_CMD_SYMBOL))

     # Command: Search for pokemon via location
    if command == "LOCATION" or command == "L":

        is_public = False
        # No arguments
        if not arguments:
            await client.send_message(message.channel, "Please specify a location, e.g. {}location Woden".format(BOT_CMD_SYMBOL))
        # Search publically (in summoned channel)
        elif arguments and arguments[0].upper() == "US":
            sendTo = message.channel
            searchTerms = arguments[1].title() # array of separate search terms
            is_public = True
        # Search privately (direct message)
        else:
            sendTo = message.author
            searchTerms = arguments[0].title() # array of separate search terms

        print('{} is smashing the DB, reverse searching for {}'.format(message.author,message.content))

        locations = ''
        pokemons = json.load(open(PATH_POKEMON_DB))
        # Trawl over every pokemon
        for pokemon in pokemons:
            mon = pokemons[pokemon]
            # Trawl over every location
            # Multiple existing locations in an array
            # NOTE: This should be replaced so that they're always in an array
            if type(mon['location']) is str:
                # Found
                if fullSearch.upper() in str(mon['location']).upper():
                    locations += '{} - {}\n'.format(pokemon, mon['location'])
            # Single existing location
            for loc in mon['location']:
                term = str(loc.upper())
                # Found
                if fullSearch.upper() in term:
                    locations += '{} - {}\n'.format(pokemon, loc)

        # No location found
        if len(locations) < 1:
            await client.send_message(sendTo, 'Sorry, nothing found for {}.\nPlease refine search term.'.format(fullSearch))
        # Location found
        else:
            await client.send_message(sendTo, 'You can find the following pokemon with **{}** in the location(s)```{}```'.format(fullSearch, locations))
            if is_public == True:
                pass
            else:
                await client.send_message(message.channel, 'Check your mailbox kiddo! :incoming_envelope:')

    # Command: Get a role ID form a role mention
    if command == "ROLEID":
        # grab first role mentioned
        firstRole = message.role_mentions[0]
        if firstRole:
            await client.send_message(message.channel, "Role '" + firstRole.name + "' ID: " + firstRole.id)

    # Command: Get Pokemon Go server status
    if command == "STATUS":
            tmp_msg = await client.send_message(message.channel, 'This will take a moment..')
            # GET from status website
            try:
                html = requests.get('http://www.mmoserverstatus.com/pokemon_go', timeout=10)
                # Load HTML content into parser
                soup = BeautifulSoup(html.content, "html.parser")
                statuses = soup.find_all("li", "white")
                # Check for a class on the status icons inside list points
                # NOTE: This does NOT check the Australian server?
                if 'fa fa-check' in str(statuses[0]):
                    await client.edit_message(tmp_msg, 'Australian server: ONLINE ')
                    print("Pokemon game server online.")
                else:
                    await client.edit_message(tmp_msg, 'Australian server: OFFLINE ')
                    print('Pokemon game server offline.')
            # GET timeout
            except (requests.exceptions.ConnectTimeout, requests.packages.urllib3.exceptions.ReadTimeoutError, requests.exceptions.ReadTimeout) as e:
                # Error handling: on site timeout advise server is most likely down
                print('P:GO Server Status Page not responding. - {}'.format(e))
                await client.send_message(message.channel, 'Server status page did not respond within 10 seconds. Server most likely down.')

    # Command: Get Canberra weather
    if command == "TEMP":
        # Send 'searching' notification
        tmp_msg = await client.send_message(message.channel, 'Cooking up an incredibly inaccurate weather reading..')
        # Authenticate to the Pyowm API
        # NOTE: Need error handling
        owm = pyowm.OWM(OWM_TOKEN)
        location = owm.weather_at_place('Canberra,AU')
        weather = location.get_weather()
        weather = weather.get_temperature('celsius')
        # Send result
        await client.edit_message(tmp_msg, 'It is currently {}°C'.format(weather['temp']))

    # Command: Assign team
    if command == "ROLE" or command == "TEAM":
        count = 0
        inTeam = False

        # Check if user is already in a team
        for role in message.author.roles:
            if 'Mystic' in role.name:
                inTeam = 'Mystic'
            elif 'Valor' in role.name:
                inTeam = 'Valor'
            elif 'Instinct' in role.name:
                inTeam = 'Instinct'

        # No argument provided
        if arguments == False:
            await client.send_message(message.channel, 'Please specify a team, e.g. **{}role blue**'.format(BOT_CMD_SYMBOL))
        # Assign admin
        elif arguments[0].upper() == 'ADMIN':
            await client.send_message(message.channel, 'http://i.imgur.com/MqxSRTm.jpg')
            await client.send_message(message.channel, 'Nice try ;)')
        # User is already in a team
        elif inTeam:
            await client.send_message(message.channel, "You're already a member of {}!\nIf this is incorrect please contact an admin.".format(inTeam))
        # Assign team
        else:
            # Look for team argument
            assignRole = False
            # Mystic / Blue
            if arguments[0].upper() == 'MYSTIC' or arguments[0].upper() == 'BLUE':
                assignRole = 'MYSTIC'
            # Valor / Red
            elif arguments[0].upper() == 'VALOR' or arguments[0].upper() == 'RED':
                assignRole = 'VALOR'
            # Instinct / Yellow
            elif arguments[0].upper() == 'INSTINCT' or arguments[0].upper() == 'YELLOW':
                assignRole = 'INSTINCT'
            # Invalid
            else:
                await client.send_message(message.channel, 'Please specify a team, e.g. **{}role blue**'.format(BOT_CMD_SYMBOL))

            # Find and assign the role object
            for role in roles:
                if role.name.upper() == assignRole:
                    assignRole = role

            # Assign role to user
            if assignRole != False:
                await client.add_roles(message.author, assignRole)
                await client.send_message(message.channel, 'Welcome to team {}!'.format(assignRole.name))

    # Command: Sing
    if command == "SING" and isAdmin(message.server.id, message.author.id):
        theme = ['I', 'want', 'to', 'be', 'the', 'very', 'best', 'like', 'no', 'one', 'ever', 'was', ':blush:']
        sing = await client.send_message(message.channel, '*clears throat*')
        for lyric in theme:
            await client.edit_message(sing, lyric)

    # Command: Restart server
    if command == "RESTART" and isAdmin(message.server.id, message.author.id):
        await client.send_message(message.channel, '<@{}> is pushing my buttons..'.format(message.author.id))
        os.execv(sys.executable, [config.PYTHON_CMD] + sys.argv)

    #Command: Kill server
    if command == "DIE" and isAdmin(message.server.id, message.author.id):
        await client.send_message(message.channel, '<@{}> is killing me..'.format(message.author.id))
        quit()

# Start Discord client
client.run(config.BOT_TOKEN)
