import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/documents.readonly',
        'https://www.googleapis.com/auth/drive.readonly']

def _get_credentials():
    """
    Internal function to get valid user credentials.
    """
    creds = None
    if os.path.exists('creds/token.json'):
        creds = Credentials.from_authorized_user_file('creds/token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'creds/credentials.json',
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open('creds/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_docs_service():
    """
    Returns an authenticated Google Docs API service client.
    """
    creds = _get_credentials()
    return build('docs', 'v1', credentials=creds)

def get_drive_service():
    """
    Returns an authenticated Google Drive API service client.
    """
    creds = _get_credentials()
    return build('drive', 'v3', credentials=creds)

def get_doc_content(doc_id):
    """
    Uses the Docs API to get the content of a document.
    """
    try:
        # Use the specific Docs service
        service = get_docs_service() 
        doc = service.documents().get(documentId=doc_id).execute()

        body = doc.get('body')
        content = body.get('content')

        full_text = read_structural_elements(content)
        return full_text
    
    except Exception as e:
        print(f"Error getting document content: {e}")
        return None
    
def read_structural_elements(elements):
    """
    Recursively reads text from a list of structural elements.
    """
    text = ""
    for value in elements:
        if 'paragraph' in value:
            para_elements = value.get('paragraph').get('elements')
            for elem in para_elements:
                if 'textRun' in elem:
                    textRun = elem.get('textRun')
                    if textRun.get('content'):
                        text += textRun.get('content')
        elif 'table' in value:
            table = value.get('table')
            for row in table.get('tableRows'):
                for cell in row.get('tableCells'):
                    text += read_structural_elements(cell.get('content'))
    return text