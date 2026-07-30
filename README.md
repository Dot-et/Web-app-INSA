>> ```bash
>> # Clone the repository
>> git clone https://github.com/Dot-et/Web-app-INSA.git
>> cd Web-app-INSA
>>
>> # Create virtual environment
>> python -m venv venv
>> source venv/bin/activate  # On Windows: venv\Scripts\activate
>>
>> # Install dependencies
>> pip install -r requirements.txt
>>
>> # Create .env file with your credentials
>> GOOGLE_CLIENT_ID=our_client_id
>> GOOGLE_CLIENT_SECRET=our_client_secret
>> SECRET_KEY=our_secret_key
>>
>> # Run the app
>> python app.py
>>