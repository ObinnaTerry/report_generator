from __future__ import print_function

from configparser import RawConfigParser
from email import encoders
import base64
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import errors

from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# If modifying these scopes, delete the file token.pickle.


class Test:
    def __init__(self):
        SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        self.file_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\\data_extract')

        """Shows basic usage of the Gmail API.
        Lists the user's Gmail labels.
        """
        parser = RawConfigParser()
        parser.read("db-creds.cfg")
        self.recipients = (parser.get('emails', "emails").strip())
        self.sender = parser.get('sender', "sender").strip()
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                print('here')
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)

    def create_message_with_attachment(self, sender, to, subject, message_text):
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject

        msg = MIMEText(message_text)
        message.attach(msg)
        print(message)
        for file_name in os.listdir(self.file_path):
            with open(f'{self.file_path}\\{file_name}', "rb") as attachment:
                part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)

            filename = os.path.basename(file_name)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            message.attach(part)

        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self):
        # //Sends an email message.
        # # Arguments:
        # # service: an authorized Gmail API service instance.
        # # user_id: User's email address. To indicate the authenticated user, the special value "me" can be used.
        # # message: Message to be sent.
        try:
            message = (self.service.users().messages().send(
                userId='me',
                body=self.create_message_with_attachment(
                    self.sender,
                    self.recipients,
                    'Invoiced Devices Report',
                    'Please see attachments'
                )).execute())
            print('Message Id: %s' % message['id'])
            return message
        except errors.HttpError as error:
            print(f'An error occurred: {error}')


f = Test()
f.send_message()
