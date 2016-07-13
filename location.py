import json
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

print(os.getcwd())

json_key = json.load(open('Google_Auth.json'))
scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name('Google_Auth.json', scope)

gc = gspread.authorize(credentials)
sheet1 = gc.open_by_url('https://docs.google.com/spreadsheets/d/1wgpGDKF4duBeeSwmZxKLAnGU2BJsvoZ5K-CGzKKZTfU/edit#gid=307024187')
wks = gc.open("Where is the money Lebowski?").sheet1
val = wks.find("Parsnip")
print('Found {} {}'.format(val.row, val.col))

587531848018-puu4bf6f62oqjm2laqrpbqif4ii5up38.apps.googleusercontent.com
