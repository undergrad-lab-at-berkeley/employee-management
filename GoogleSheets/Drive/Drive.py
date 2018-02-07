from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('drive', 'v3', http=http)

# We want to only create a new directory when adding a new group?
# We want to test creating a directory for entirety of ULAB?

# If true, group already in directory and subdirectories, false otherwise
def check_group(name, parentId='1sv8_MI_b-JUdX0_ci6tj-RiF3dT3_ddB'):
    query = """trashed=false and '""" + parentId + "'" + """ in parents"""
    files = service.files().list(fields="files(name, id)", q=query).execute()
    groups = files.get('files')
    for group in groups:
        if name == group.get('name'):
            return True
        elif check_group(name, group.get('id')):
            return True
    return False

def create_new_directory(name, subgroups={}, parentId='1sv8_MI_b-JUdX0_ci6tj-RiF3dT3_ddB'):
    # Checks if group is subgroup in parent by one level
    if not check_group(name):
        newGroup_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parentId]
        }
        newGroup = service.files().create(body=newGroup_metadata, fields='id').execute()
        newGroupId = newGroup['id']

        # if subgroups != {}:
        #     for subgroup in subgroups:
        #         create_new_directory(subgroup, {}, newGroupId)

        ### adds edit privileges to file/folder
        add_permissions('khang.nguyencampbell@gmail.com', newGroupId)
        return
    print('Group already in directory')

def get_group_id(group_name):
    query = """trashed=false and name='""" + group_name + """'"""
    results = service.files().list(pageSize=10, fields="nextPageToken, files(id, name)", q=query).execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        return items[0]['id']

def get_permission_id(email_address, group_name):
    group_id = get_group_id(group_name)
    response = service.permissions().list(fileId=group_id, fields="permissions(id, emailAddress)").execute()
    perms = response.get('permissions')
    for perm in perms:
        if perm['emailAddress'] == email_address:
            return perm['id']

def add_permissions(email_address, newGroupId):
    permissions = {
        'role': 'writer',
        'type': 'user',
        'emailAddress': email_address
    }

    add_pm = service.permissions().create(fileId=newGroupId,
                body=permissions, sendNotificationEmail=False).execute()

def remove_permissions(email_address, group_name):
    group_id = get_group_id(group_name)
    perm_id = get_permission_id(email_address, group_name)
    del_pm = service.permissions().delete(fileId=group_id, permissionId=perm_id).execute()
    return