import json
from socket import socket
from sys import exit


def send_message(msg, conn, delimiter=';;', encoding='utf-8'):
    try:
        conn.send((msg + delimiter).encode(encoding))
    except ConnectionResetError:
        print('Connection aborted by host while waiting request')
        exit(-1)


def receive_message(conn, delimiter=';;', encoding='utf-8'):
    msg = ''
    while not msg.endswith(delimiter):
        try:
            msg += conn.recv(1024).decode(encoding)
        except ConnectionError:
            print('Connection aborted')
            return
    msg = msg[:-len(delimiter)]
    return json.loads(msg)


sock = socket()
host = 'localhost'
port = 32280

try:
    sock.connect((host, port))
except ConnectionRefusedError:
    print(f'"{host}:{port}" is not available')
else:
    request = ''
    while request != 'quit':
        request = input('Enter your request: ')

        send_message(request, sock)
        if request == 'quit':
            sock.close()
            continue

        answer = receive_message(sock)
        if type(answer) == list:
            if len(answer) == 0:
                print('Совпадений не найдено.')
            else:
                print(f'Найдено {len(answer)} совпадений:')
                print(''.join(answer))
        else:
            print('Вот, что вернул сервер:', answer)
        print()


# test1
# Enter your request: 23-Ticket
# Найдено 493 совпадений:
# [Sun Apr  2 23:46:59 2017][Error][Kernel::System::Ticket::TicketSubjectClean][1136] Need TicketNumber!
# [Sun Apr  2 23:46:59 2017][Error][Kernel::System::Ticket::TicketPermission][3854] Need TicketID!
# [Sun Apr  2 23:46:59 2017][Error][Kernel::System::Ticket::TicketPermission][3854] Need TicketID!
# [Sun Apr  2 23:46:59 2017][Error][Kernel::System::Ticket::TicketPermission][3854] Need TicketID!
# ...

# test2
# Enter your request: 23:42-Ticket
# Найдено 22 совпадений:
# [Mon Apr  3 23:42:11 2017][Error][Kernel::System::Ticket::Article::ArticleGet][1963] No such article for TicketID (12855914)!
# [Mon Apr  3 23:42:11 2017][Error][Kernel::System::Ticket::TicketGet][1309] Need TicketID!
# [Mon Apr  3 23:42:11 2017][Error][Kernel::System::Ticket::TicketPermission][3854] Need TicketID!
# [Mon Apr  3 23:42:12 2017][Error][Kernel::System::Ticket::TicketPermission][3854] Need TicketID!
# ...

# test3
# Enter your request: 23:42:11-Ticket
# Найдено 3 совпадений:
# [Mon Apr  3 23:42:11 2017][Error][Kernel::System::Ticket::Article::ArticleGet][1963] No such article for TicketID (12855914)!
# [Mon Apr  3 23:42:11 2017][Error][Kernel::System::Ticket::TicketGet][1309] Need TicketID!
# [Mon Apr  3 23:42:11 2017][Error][Kernel::System::Ticket::TicketPermission][3854] Need TicketID!

# test4
# Enter your request: 23:42:14-Ticket
# Совпадений не найдено.
