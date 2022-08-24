# Password_Hacker
A proof-of-concept password hacker in Python developed alongside the JetBrains/Hyperskill project of the same name.

Takes arguments of domain and port from the command line, then establishes a mock connection with your
local production environment to attempt to 'hack' a password via different methods, including brute force,
common password dictionary, and a time based attack. The script interfaces with a test environment, so running it standalone
won't do anything.
