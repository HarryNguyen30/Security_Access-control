## Flask Authentication and Access Control System
This project is a Flask- based HTTP sever that implements users authentication, multi-factor authentication (MFA), and access control using security level based on Biba access control model

## Setup instruction
To run these programs you will need to install a recent version of python3, preferably version 3.7 or higher.

Next you will need to install the required libraries using the pip tool included with python, run the following in a terminal in this folder:

```sh
pip install -r requirements.txt
```

Now you're ready to run the programs.


## Running the programs
First we need to running the server:

```sh
python3 server.py
```
OR
```sh
python server.py
```

It will say that is running on http://127.0.0.1:2250, which means you are ready to start the client with:

```sh
python3 client.py
```
OR
```sh
python client.py
```
The client goes through and interact with server.

## Features
User Authentication: Secure user login with password hasing (using bcrypt).
Multi-factor Authentication (MFA): Two-step verification via email.
Role-base Access: Admin and clients roles with different
Admin Console: Admin can add, modify, and delete users.
Client Console: Client can audit expenses, timesheets, meeting minutes and more, depending on their security level.
Resoucre Access Control: Resouces are protected based on user security levels.
Session Management: Token-based session management with expiration times.