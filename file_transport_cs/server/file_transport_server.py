from socket import socket
from os import path
from threading import Thread


def get_optimal_buff_size(file_size):  # сам придумал, вроде работает
    min_buff = 4096  # 2 ** 12 - 4кб
    max_buff = 1048576  # 2 ** 20 - 1мб
    optimal_buff = file_size // 1000

    if min_buff < optimal_buff < max_buff:
        power = 0
        while optimal_buff:
            optimal_buff //= 2
            power += 1
        return 2 ** power
    elif optimal_buff < min_buff:
        return min_buff
    elif optimal_buff > max_buff:
        return max_buff


def send_answer(msg, conn, filename, status='200', buff_size=65536, encoding='utf-8'):
    def send_head(conn, **kwargs):
        delimiter = ';;'
        head_str = ''
        for key, value in kwargs.items():
            head_str += f'{key}={value}' + delimiter
        head_str = head_str[:-len(delimiter)]  # убираем последний, лишний delimiter

        conn.send(head_str.encode(encoding))
        accepted = conn.recv(8)  # ожидается b'true' или что-то другое, не больше 8 байт
        return accepted

    def send_file(conn, msg_type='file'):
        msg_len = path.getsize(filename)
        buff_size = get_optimal_buff_size(msg_len)
        accepted = send_head(conn, type=msg_type, status=status, len=msg_len, filename=filename, buff_size=buff_size)

        if accepted == success_status:
            total_sent = 0
            i = 0
            while total_sent < msg_len:
                sent = conn.send(msg.read(buff_size))
                accepted = conn.recv(8)
                if accepted == success_status:
                    total_sent += sent
                i += 1
                if i == 20:
                    print(total_sent)

    def send_exception(conn, msg_type='exception'):
        msg_len = len(msg)
        accepted = send_head(conn, type=msg_type, status=status, len=msg_len, filename=filename, buff_size=buff_size)

        if accepted == success_status:
            total_sent = 0
            while total_sent < msg_len:
                sent = conn.send(msg[total_sent:total_sent + buff_size])
                accepted = conn.recv(8)
                if accepted == success_status:
                    total_sent += sent

    success_status = b'true'  # этот статус вернёт клиент, если удачно примет чанк

    try:
        if status == '200':
            send_file(conn)
        else:
            send_exception(conn)
    except BaseException:
        return
    else:
        return True


def start_server(host_port):
    def serve_client(conn, addr):
        while True:
            try:
                filename = conn.recv(1024).decode()
            except ConnectionResetError:
                filename = ''

            if filename == 'quit' or filename == '':
                break

            try:
                file = open(filename, 'rb')
            except BaseException as err:
                statuses = {
                    'PermissionError': '403',
                    'FileNotFoundError': '404'
                }
                err_type = type(err).__name__
                err_description = err.args[1]

                print(f'{addr}:', '|||', err_type, '|||', err_description)

                sent = send_answer(f'{err_type}! {err_description}'.encode(), conn, filename, status=statuses.get(err_type, '500'))
            else:
                sent = send_answer(file, conn, filename)
                file.close()
            finally:
                if not sent:
                    break

        print(f'{addr}: Disconnected')

    def main():
        while True:
            conn, addr = sock.accept()
            addr = addr[0]
            print(f'Connected to "{addr}"')
            Thread(target=serve_client, args=(conn, addr)).start()

    with socket() as sock:
        try:
            sock.bind(host_port)
        except ConnectionError:
            print(f'Cant bind server to {host_port[0]}:{host_port[1]}')
            return

        sock.listen(10)
        main()


HOST = 'localhost'
PORT = 32280
start_server((HOST, PORT))
