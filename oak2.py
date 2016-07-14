import asyncio
import sys
import os
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import discord
import requests
from bs4 import BeautifulSoup
from discord import role


client = discord.Client()

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
    roles = []
    for role in server.roles:
        print(role.name + ' (' + role.id + ')')


@client.event
async def on_member_join(member):
    print("new {}".format(member))
    await client.send_message(member.channel, 'Welcome {}'.format(member))

@client.event
async def on_message(message):
    if message.content.startswith('!help'):
        _help = '**Assigning team:**\n!role @teamname\n\n**Finding a Pokemon:**\n!find Pokemon_Name\n\n**Server status:**\n!status\n\nMore to come! If you have any feature requests message @Mirokoth'
        await client.send_message(message.channel, '{}'.format(_help))

    if message.content.startswith('!find'):
            await client.send_message(message.channel, 'Searching...\n')

            son_key = json.load(open('C:\\Users\\rhyse\\Google Drive\\Projects\\Prof-Oak\\Google_Auth.json'))
            scope = ['https://spreadsheets.google.com/feeds']
            credentials = ServiceAccountCredentials.from_json_keyfile_name('C:\\Users\\rhyse\\Google Drive\\Projects\\Prof-Oak\\Google_Auth.json', scope)
            gc = gspread.authorize(credentials)
            sheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1xGH7HNNZvrOlAd1U1RogF4hlMlmN-gSFbeBpZ0gpnBY/edit#gid=0')
            wks = sheet.get_worksheet(0)
            _term = message.content.replace('!find ', '').title()
            _term = _term.title()
            if 'Oak' in _term:
                await client.send_file(message.channel, 'C:\\Users\\rhyse\\Google Drive\\Projects\\Prof Oak\\Oak1.png')

            try:
                _result = wks.find(_term)
            except gspread.exceptions.CellNotFound as e:
                await client.send_message(message.channel, 'Sorry but we could not find {}. Please confirm name'.format(_term))
            _output = wks.cell(_result.row, _result.col+1).value
            _output = _output.replace(',', '\n')
            print(_term)

            await client.send_message(message.channel, '{} can be found at:\n```\n {} \n\n Data from - https://goo.gl/cr7ErJ```'.format(_term, _output))



    if message.content.startswith('!roleid'):
        # grab first role mentioned
        firstRole = message.role_mentions[0]
        if firstRole:
            await client.send_message(message.channel, "Role '" + firstRole.name + "' ID: " + firstRole.id)


    if message.content.startswith('!Role') or message.content.startswith('!role'):
        _tmp_count = 0
        for role in message.role_mentions:
            if 'Admin' in role.name:
                _tmp_count =+ 5
                await client.send_message(message.channel, 'http://i.imgur.com/MqxSRTm.jpg')

        #for role in message.author.roles:
            #if 'Mystic' in role.name:
                #_tmp_count =+ 1
            #elif 'Valor' in role.name:
                #_tmp_count =+ 1
            #elif 'Instinct' in role.name:
                #_tmp_count =+ 1

        if _tmp_count >= 5:
                await client.send_message(message.channel, 'Nice Try')
        if _tmp_count == 0:
                await client.add_roles(message.author, server.roles[1])
                #await client.add_roles(message.author, message.role_mentions[0])
                await client.send_message(message.channel, 'Welcome to team {}!'.format(message.role_mentions[0]))
        else:
            print(_tmp_count)
            await client.send_message(message.channel, 'It looks like you already have a team.\nIf you think this is an error please let us know')


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


    if message.content.startswith('!quit'):
        await quit()


client.run('MjAyNjg0ODc4NjYyMTM5OTA0.Cmd-CA.rrfgsulJnqTzvz0ss9T-PzAyWgM')
