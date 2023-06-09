from __future__ import print_function

import os.path
import os
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import csv

bfwLogsPath = "ubuntu@ec2-52-21-241-87.compute-1.amazonaws.com:bfw/logs/"
environmentWL = "WL"
environmentOTA = "OTA"
downloadFilePath = "BFWLogs/"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
tokenJsonFilePath = "Security/token.json"

#Software configurations
MAY_LOGS_FILES = ["MAY-18-2023", "MAY-19-2023", "MAY-20-2023", "MAY-21-2023"]
JUNE_LOGS_FILES = ["JUNE-22-2023", "JUNE-23-2023", "JUNE-24-2023", "JUNE-25-2023"]

MAY_OTA_SPREADSHEET_ID = "136nlvD8cn4eqC0P2KTHmTHQjs1HdGj82v4InfMo-Jts"
MAY_WL_SPREADSHEET_ID = "136nlvD8cn4eqC0P2KTHmTHQjs1HdGj82v4InfMo-Jts"

SPREADSHEET_LOGS = [[MAY_WL_SPREADSHEET_ID, environmentWL, MAY_LOGS_FILES],
                    [MAY_OTA_SPREADSHEET_ID, environmentOTA, MAY_LOGS_FILES]]
SHEET_CLEAR_NAME = 'Log completo'
WRITE_SAMPLE_RANGE = 'Log completo!A1'
READ_SAMPLE_RANGE = 'CONSOLIDAÇÃO!A2:B'

#PC configurations
pemFilePath = "~/.ssh/automatizador.pem"
clientSecretJsonFilePath = "Security/client_secret_1078850008607-88q9v0b539des6clkluh816fchb26m8b.apps" \
                           ".googleusercontent.com.json"
def googleAPIAuthentication():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(tokenJsonFilePath):
        creds = Credentials.from_authorized_user_file(tokenJsonFilePath, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                clientSecretJsonFilePath, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(tokenJsonFilePath, 'w') as token:
            token.write(creds.to_json())
    return creds

def readGoogleSheet(creds, spreadSheetId):
    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadSheetId,
                                    range=READ_SAMPLE_RANGE).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        print('Order ID, Devolução:')
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            print('%s, %s' % (row[0], row[1]))
    except HttpError as err:
        print(err)

def writeBFWLogsOnGoogleSheet(creds, spreadSheetId, values):
    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()

        # Clear sheet
        service.spreadsheets().values().clear(spreadsheetId=spreadSheetId, range=SHEET_CLEAR_NAME, body={}).execute()

        #Update values
        sheet.values().update(spreadsheetId=spreadSheetId,
                                    range=WRITE_SAMPLE_RANGE, valueInputOption="USER_ENTERED",
                                    body={"values":values}).execute()
    except HttpError as err:
        print(err)
def downloadBFWLogs(enviroment, logsDate):
    for logDate in logsDate:
        os.system("scp -i " + pemFilePath + " " + bfwLogsPath + enviroment + "-" + logDate + ".csv " + downloadFilePath + enviroment + "-" + logDate + ".csv")
def readBFWLogs(enviroment, logsDate):
    logs = []
    for logDate in logsDate:
        with open(downloadFilePath + "/" + enviroment + "-" + logDate + ".csv", newline='') as csvfile:
            if len(logs):
                logs = logs + (list(csv.reader(csvfile, delimiter=';'))[1:])
            else:
                logs = logs + (list(csv.reader(csvfile, delimiter=';')))
    return logs

#Turn ON VPN!
if __name__ == '__main__':
    print('Starts Google API authentication')
    creds = googleAPIAuthentication()
    print("Authentication completed successfully")
    for spreadSheetConfig in SPREADSHEET_LOGS:
        spreadSheetId = spreadSheetConfig[0]
        environment = spreadSheetConfig[1]
        logsDate = spreadSheetConfig[2]
        print('Starts BFW logs downloads')
        downloadBFWLogs(environment, logsDate)
        print("Downloads completed successfully")
        print("Starting to read the BFW logs file")
        logs = readBFWLogs(environment, logsDate)
        print("BFW Logs file read completed successfully")
        print("Starting to write the BFW logs on google sheets")
        writeBFWLogsOnGoogleSheet(creds, spreadSheetId, logs)
        print("Writing of BFW logs in Google spreadsheets completed successfully")
        #print('Starts read Google Sheet')
        #readGoogleSheet(creds, spreadSheetId)
        time.sleep(20)


#Documentações base:
#https://www.hashtagtreinamentos.com/integracao-do-google-sheets-com-python?gad=1&gclid=CjwKCAjwpuajBhBpEiwA_ZtfhWJAknnTFYROR0lrlDTBLx0KAeUsxcpB7XXdNYawZGuY42eIvXkI7hoCsuAQAvD_BwE
#https://developers.google.com/sheets/api/quickstart/python?hl=pt-br
#https://developers.google.com/sheets/api/guides/batchupdate?hl=pt-br
#https://www.youtube.com/watch?v=4ssigWmExak&t=2s
