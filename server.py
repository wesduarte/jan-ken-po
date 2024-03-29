import sys, socket, select

HOST = '' 
SOCKET_LIST = []
players_dict = {}
answers_dict = {}
RECV_BUFFER = 4096 
PORT = 9009
OPTIONS = {
    'rock' : 0,
    'paper' : 1,
    'scissors' : 2
}

def game_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(4)
 
    # add server socket object to the list of readable connections
    SOCKET_LIST.append(server_socket)
 
    print "Jan-ken-Po!\nChoose among rock, paper and scissors:" + str(PORT)
 
    while 1:

        # get the list sockets which are ready to be read through select
        # 4th arg, time_out  = 0 : poll and never block
        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)

      
        for sock in ready_to_read:
            # a new connection request recieved
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                player_number = len(SOCKET_LIST)-1
                players_dict[sockfd] = player_number
                
                if(len(players_dict) < 3):
                    print "Player %s connected" % (player_number)
                    broadcast(server_socket, sockfd, "Player %s entered\n" % (player_number))
                else:
                    print "Spectator %s connected" % (4-player_number)
                    broadcast(server_socket, sockfd, "Spectator %s entered\n" % (4-player_number))
             
            # a message from a client, not a new connection
            else:
                # process data recieved from client, 
                try:
                    # receiving data from the socket.
                    data = sock.recv(RECV_BUFFER)
                    if len(players_dict.values()) > 2:
                        if data:
                            option = parse_response(data)
                            check = option in OPTIONS.keys()

                            player_number = players_dict[sock]
                            
                            if(check_option(option) and player_number < 3):
                                answers_dict[player_number] = OPTIONS[option]
                                answers = answers_dict.values()
                                current_player = "Player %s" % player_number
                                cast_message = "[%s] - %s did his cast\n" % (str(sock.getpeername()), current_player)
                                broadcast(server_socket, sock, cast_message)
                                for player_number in players_dict.values():
                                    if player_number > 2:
                                        spectator_index = players_dict.values().index(player_number)
                                        spectator = players_dict.keys()[spectator_index]
                                        private_cast_message = "%s choose %s" % (current_player, data)
                                        spectator.send(private_cast_message)

                                if(len(answers) == 2):
                                    print check_result(answers)
                                    broadcast(server_socket, server_socket, check_result(answers))
                                    answers_dict.clear()

                            elif(player_number >= 3):
                                # Spectators do not play, they just watch the game
                                pass
                            else:
                                sock.send('invalid option! Choose another!\n')
                        else:
                            # remove the socket that's broken    
                            if sock in SOCKET_LIST:
                                players_dict.pop(sock, None)
                                SOCKET_LIST.remove(sock)

                            update_players_number(players_dict)

                            # at this stage, no data means probably the connection has been broken
                            broadcast(server_socket, sock, "Client (%s, %s) is offline\n" % addr) 
                    else:
                        sock.send('Waiting for spectators!\n')

                # exception 
                except Exception as e:
                    print e
                    players_dict.pop(sock, None)
                    update_players_number(players_dict)
                    broadcast(server_socket, sock, "Client (%s, %s) is offline\n" % addr)
                    continue

    server_socket.close()
    
# broadcast game messages to all connected clients
def broadcast (server_socket, sock, message):
    for socket in SOCKET_LIST:
        # send the message only to peer
        if socket != server_socket and socket != sock :
            try :
                socket.send(message)
            except :
                # broken socket connection
                socket.close()
                # broken socket, remove it
                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)

def check_result(answers):
    result_table = [[-1, 1, 0], [1, -1, 2], [0, 2, -1]]
    op1, op2 = answers
    winner_option_value = result_table[op1][op2]
    if winner_option_value == -1:
        return 'Draw Game!\n'
    else:
        winner_option_index = OPTIONS.values().index(winner_option_value)
        winner_option = OPTIONS.keys()[winner_option_index]
        winner_player_index = answers_dict.values().index(winner_option_value)
        winner_player = answers_dict.keys()[winner_player_index]
        return "Winner is player %s with option %s!\n" % (winner_player, winner_option)

def parse_response(data):
    parsed_data = data.split('\n')[0]
    return parsed_data

def check_option(option):
    if option in OPTIONS.keys():
        return True
    else:
        return False

def update_players_number(players_number_dict):
    for i in range(1, len(SOCKET_LIST)):
        sock = SOCKET_LIST[i]
        players_number_dict[sock] = i
 
if __name__ == "__main__":

    sys.exit(game_server())


