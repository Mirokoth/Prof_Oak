import json
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

print(os.getcwd())

json_key = json.load(open('C:\\Users\\rhyse\\Google Drive\\Projects\\Prof-Oak\\Google_Auth.json'))
scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name('C:\\Users\\rhyse\\Google Drive\\Projects\\Prof-Oak\\Google_Auth.json', scope)

gc = gspread.authorize(credentials)
sheet1 = gc.open_by_url('https://docs.google.com/spreadsheets/d/1Sbjy1vp-W64as2VRJWIrShwFAO3D9Jf9xWqLILt7dJE/edit#gid=0')
#wks = gc.open("Pokemon GO Canberra").sheet1
wks = sheet1.get_worksheet(0)
val = wks.find("Squirtle")

print('Found {} {}'.format(val.row, val.col))
print(wks.cell(val.row, val.col+3).value)
