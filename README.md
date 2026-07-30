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
>> GOOGLE_CLIENT_ID=your_client_id
>> GOOGLE_CLIENT_SECRET=your_client_secret
>> SECRET_KEY=your_secret_key
>>
>> # Run the app
>> python app.py
>>