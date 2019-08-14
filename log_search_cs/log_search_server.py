import json
from socket import socket
from threading import Thread


def make_log_dict_by_filename(filename):  # 'otrs_error.log'
    from collections import defaultdict

    def get_hour_minute_second(line):
        try:
            date = line[line.find('[') + 1: line.find(']')] if ~line.find('[') else None
        except (ValueError, TypeError):
            print('Incorrect line')
            return
        try:
            hour, minute, second = date.split('  ')[1].split()[1].split(':')
        except (IndexError, AttributeError):
            print(f'Incorrect line {line}')
            return
        return hour, minute, second

    res_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    with open(filename) as file:
        for line in file:
            hms = get_hour_minute_second(line)
            if hms is None:
                continue
            res_dict[hms[0]][hms[1]][hms[2]].append(line)

    return res_dict


def get_log_list_by_module_and_time(module, time_params):
    time_params_len = len(time_params)
    res_lst = []

    if time_params_len == 1:
        hour = time_params[0]
        for seconds_dict in log_dict[hour].values():
            for log_string_list in seconds_dict.values():
                for log_string in log_string_list:
                    if module in log_string:
                        res_lst.append(log_string)
    elif time_params_len == 2:
        hour, minute = time_params[0], time_params[1]
        for log_string_list in log_dict[hour][minute].values():
            for log_string in log_string_list:
                if module in log_string:
                    res_lst.append(log_string)
    elif time_params_len == 3:
        hour, minute, second = time_params[0], time_params[1], time_params[2]
        for log_string in log_dict[hour][minute][second]:
            if module in log_string:
                res_lst.append(log_string)

    return res_lst


def send_message(msg, conn, delimiter=';;', encoding='utf-8'):
    try:
        conn.send((json.dumps(msg) + delimiter).encode(encoding))
    except ConnectionResetError:
        print('Sending fault.')


def receive_message(conn, delimiter=';;', encoding='utf-8'):
    msg = ''
    while not msg.endswith(delimiter):
        try:
            msg += conn.recv(1024).decode(encoding)
        except ConnectionResetError:
            print('Receiving fault.')
            break
    else:
        msg = msg[:-len(delimiter)]
    return msg


def serve_client(conn):
    def get_time_params_and_module_by_request(request):
        try:
            time, module = request.split('-')
        except ValueError:
            return  # If request format is incorrect returns None

        time_params = time.split(':')
        for el in time_params:
            if not el.isdigit():
                return

        return time_params, module

    request = receive_message(conn)
    while request != 'quit':
        tm_result = get_time_params_and_module_by_request(request)
        if tm_result is None:
            send_message('Request format is incorrect', conn)
        else:
            time_params, module = tm_result[0], tm_result[1]
            result_list = get_log_list_by_module_and_time(module, time_params)
            send_message(result_list, conn)

        request = receive_message(conn)


log_dict = make_log_dict_by_filename('otrs_error.log')

sock = socket()
host = 'localhost'
port = 32280
sock.bind(('localhost', 32280))
sock.listen(10)

print(f'Server based on {host}:{port}')

while True:
    conn, addr = sock.accept()
    print(f'Connected to "{addr[0]}"')
    Thread(target=serve_client, args=(conn, )).start()
