from socket import socket
import shelve
from sys import exit


def load_from_server(conn, filename, db):
    '''Скачивает файл filename с сервера по активному соединению conn и загружает его в БД db.
    Если всё прошло успешно, возвращает True'''

    def receive_answer(conn, encoding='utf-8'):
        success_status = b'true'

        head_str = conn.recv(2048).decode(encoding)
        conn.send(success_status)

        msg_args = dict([key_value.split('=') for key_value in head_str.split(';;')])

        msg_len = int(msg_args['len'])
        filename = msg_args['filename']
        buff_size = int(msg_args['buff_size'])
        total_recv = 0

        if msg_args['status'] == '200':
            db[filename] = b''

            while total_recv < msg_len:
                chunk = conn.recv(buff_size)
                conn.send(success_status)
                total_recv += len(chunk)
                db[filename] += chunk

            return True
        else:
            try:
                db[filename]
            except KeyError:
                pass  # в сообщений ниже и так будет информация об ошибке
            else:
                print("File is already in database, but it's not available now or server is broken...")

            msg = b''
            while total_recv < msg_len:
                chunk = conn.recv(buff_size)
                total_recv += len(chunk)
                conn.send(success_status)
                msg += chunk

            print(f'An error has occurred: "status={msg_args["status"]}: {msg.decode(encoding)}"')

    try:
        conn.send(filename.encode())
        return receive_answer(conn)
    except ConnectionError as err:
        print(err.args[1])


def replace_from_db(db, db_filename, local_filename, buff_size=16384):
    total_moved = 0
    file_size = len(db[db_filename])

    with open(local_filename, 'wb') as file:
        while total_moved < file_size:
            file.write(db[db_filename][total_moved:total_moved + buff_size])
            total_moved += buff_size

    print(f'File "{db_filename}" replaced on "{local_filename}" local path from database')


def check_command(command):
    if len(command) > 0:
        if command[0] == 'get':
            return len(command) == 2
        elif command[0] == 'cp':
            return len(command) == 3
        elif command[0] == 'quit':
            return True


def request_port():
    try:
        port = int(input('Enter port: '))
    except ValueError:
        print('Port must be integer')
        return request_port()
    else:
        return port


def exit_by_exception(exception_desc):
    print(exception_desc)
    input()
    exit(0)


def main_loop(sock, db):
    while True:
        command = input('Enter your command: ').split()

        if check_command(command):
            if command[0] == 'get':
                loaded = load_from_server(sock, command[1], db)
                if loaded:  # в ином случае иформация об ошибке и так будет выдана функцией load_from_server
                    print(f'File "{command[1]}" was successfully received')

            elif command[0] == 'cp':
                try:
                    db[command[1]]
                except KeyError:
                    loaded = load_from_server(sock, command[1], db)
                    if loaded:
                        replace_from_db(db, command[1], command[2])
                    else:
                        print('"cp" command fault')
                else:
                    replace_from_db(db, command[1], command[2])

            elif command[0] == 'quit':
                break
        else:
            print('Incorrect command!')
        print()


HOST = input('Enter host: ')  # 'localhost'
HOST = HOST if HOST else 'localhost'  # это очень смешно читать
PORT = request_port()  # 32280

host_port = (HOST, PORT)
db_name = 'local.db'

with socket() as sock:
    try:
        sock.connect(host_port)
    except ConnectionError:
        exit_by_exception('Server is not available')
    except OSError:
        exit_by_exception('Incorrect address')

    with shelve.open(db_name) as db:
        main_loop(sock, db)
