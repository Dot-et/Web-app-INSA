from app import app
from flask import url_for

with app.app_context():
    with app.test_request_context():
        redirect_uri = url_for('google_callback', _external=True)
        print("=" * 50)
        print("My redirect URI is:")
        print(redirect_uri)
        print("=" * 50)
        print("\nAdd this EXACT URI to Google Cloud Console:")
        print(f"Under 'Authorized redirect URIs' add: {redirect_uri}")
