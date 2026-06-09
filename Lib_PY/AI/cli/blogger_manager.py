"""
Library:      lib_blogger_manager.py
Family:       AI
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Integration manager for Google Blogger API and content publishing.
"""

import os
import sys
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class BloggerManager:
    def __init__(self, client_secret_path, state_path):
        self.client_secret_path = client_secret_path
        self.state_path = state_path
        self.scopes = ['https://www.googleapis.com/auth/blogger']
        self.token_path = os.path.expanduser("~/.env/blogger_token.json")
        self.service = None

    def authenticate(self):
        """Handles the OAuth 2.0 flow and returns a Blogger service object."""
        creds = None
        
        # 1. Try loading existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)

        # 2. If no valid creds, refresh or run flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_path, self.scopes)
                # In Termux, this might need manual copy-paste if browser fails
                creds = flow.run_local_server(port=0, open_browser=False)
            
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('blogger', 'v3', credentials=creds)
        return True

    def list_blogs(self):
        """Lists all blogs for the authenticated user."""
        if not self.service: self.authenticate()
        return self.service.blogs().listByUser(userId='self').execute()

    def create_post(self, blog_id, title, content, is_draft=True):
        """Creates a new post."""
        if not self.service: self.authenticate()
        body = {
            "kind": "blogger#post",
            "title": title,
            "content": content
        }
        return self.service.posts().insert(blogId=blog_id, body=body, isDraft=is_draft).execute()

    def update_post(self, blog_id, post_id, title=None, content=None):
        """Updates an existing post."""
        if not self.service: self.authenticate()
        body = {}
        if title: body["title"] = title
        if content: body["content"] = content
        return self.service.posts().patch(blogId=blog_id, postId=post_id, body=body).execute()

    def delete_post(self, blog_id, post_id):
        """Deletes a post."""
        if not self.service: self.authenticate()
        self.service.posts().delete(blogId=blog_id, postId=post_id).execute()
        return True

if __name__ == "__main__":
    pass
