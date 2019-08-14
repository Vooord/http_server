import argparse
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread
from client import Client, responses
from time import ctime


class MyBaseHTTPServer(object):
    def __init__(self, host_port):
        self.sock = socket()
        try:
            self.sock.bind(host_port)
        except ValueError:
            print(f'Initial error. Incorrect host/port')
        else:
            print(f'Sever based on {host_port[0]}:{host_port[1]}')

            self.host = host_port[0]
            self.port = int(host_port[1])
            self.http_ver = 'HTTP/1.1'

            self.access_log = 'access.log'
            self.error_log = 'error.log'
            self.clients = {}


    def make_log(self, client, request, answer, err=False):
        if request is None or answer is None:
            return

        if not err:
            if client.log_type == 'long':
                logged_request = [(key, value) for key, value in request.items()]
            else:
                logged_request = [(key, value) for key, value in request.items() if key in ['method', 'path', 'Cookie']]
            logged_request = "   ".join([f"{key}: {value}" for key, value in logged_request])
            logged = f'[{client.addr}][{ctime()}][{logged_request}][{answer["status_code"]}][{answer.get("Content-Length", 0)}]\r'

            with open(self.access_log, 'a') as access_log:
                access_log.write(logged)
        else:
            with open(self.error_log, 'a') as error_log:
                logged = f'[{client.addr}][{ctime()}][{answer["status_code"]}][{answer["msg"]}]\r'
                error_log.write(logged)


    def make_default_answer_dict(self, status_code, msg):
        answer = {
            'http_version': self.http_ver,
            'status_code': status_code,
            'reason_phrase': responses.get(status_code),
            'msg': msg
        }

        return answer


    def fatal_error(self, client, conn, status_code, msg):
        answer = self.make_default_answer_dict(status_code, msg)
        self.process_response(client, conn, answer)
        self.make_log(client, '', answer, err=True)
        self.sock.close()
        raise ConnectionResetError


    def process_response(self, client, conn, answer):
        def make_answers_html():
            body = f'''<!DOCTYPE HTML>
            <html>
                <head>
                    <meta content="text/html; charset=utf-8">
                </head>
                <body bgcolor={client.cookie["bg_color"]}>
                    {answer['msg']}
                    <p><a href="/">Start Menu</a></p>'
                </body>
            </html>'''
            return body

        if answer is None:
            try:
                conn.close()
            except ConnectionError:
                pass
            finally:
                return

        starting_string = f"{answer['http_version']} {answer['status_code']} {answer['reason_phrase']}\r\n".encode()
        
        headers = 'Server: MyBaseHTTPServer\r\n'.encode()
        headers += 'Content-Type: text/html; charset=utf-8\r\n'.encode()
        
        cookie = '; '.join([f'{key}={value}' if key.lower() not in ('secure', 'httponly') else key for key, value in client.cookie.items()])
        headers += f'Cookie: {cookie}\r\n'.encode()
        
        msg_body = make_answers_html().encode()
        headers += f'Content-Length: {len(msg_body)}\r\n'.encode()

        headers += '\r\n'.encode()

        try:
            conn.send(starting_string + headers + msg_body)
        except ConnectionError:
            answer['Content-Length'] = 0
        else:
            answer['Content-Length'] = len(msg_body)  # делается для make_log на будущее


    def process_request(self, client, request):
        '''Обрабатывает request и возвращает словарь answer.
        Если request передан как None, вернётся None.'''

        def get_start_menu():
            with open('start_menu.html') as f:
                return self.make_default_answer_dict(200, f.read())

        def change_log_type():
            try:
                if int(path_dirs[2]):
                    client.log_type = 'short'
                else:
                    client.log_type = 'long'
            except ValueError as err:
                answer = self.make_default_answer_dict(500, f'Incorrect log-type value (use "1" to "long" or "0" to "short")')
                if client.show_errors: answer['msg'] += f'\nServer returned: {err.args[0]}'
            else:
                return self.make_default_answer_dict(200, f'Log file changed to "{client.log_type}"')

        def change_errors_msgs():
            try:
                client.show_errors = int(path_dirs[2])
            except ValueError as err:
                answer = self.make_default_answer_dict(500, f'Incorrect value (use "1" or "0")')
                if client.show_errors: answer['msg'] += f'\nServer returned: {err.args[0]}'
            else:
                return self.make_default_answer_dict(200, 'You will now see system errors' if client.show_errors else 'Now you will not see system errors')

        def divide():
            try:
                dividend, divider = int(path_dirs[2]), int(path_dirs[4])
                quotient = dividend / divider
            except IndexError as err:
                answer = self.make_default_answer_dict(500, f'Incorrect URI structure ("/div/smth/to/smth" expected)')
                if client.show_errors: answer['msg'] += f'\nServer returned: {err.args[0]}'
            except ValueError as err:
                answer = self.make_default_answer_dict(500, f'Incorrect dividend or divider in requests URI "{request["path"]}"')
                if client.show_errors: answer['msg'] += f'\nServer returned: {err.args[0]}'
            except ZeroDivisionError as err:
                answer = self.make_default_answer_dict(500, f'Division by zero not supported')
                if client.show_errors: answer['msg'] += f'\nServer returned: {err.args[0]}'
            else:
                answer = self.make_default_answer_dict(200, f'Requested operation is "{dividend} / {divider} = {quotient}"')
            finally:
                return answer

        def set_cookie():
            from re import sub

            try:
                c = {sub(r'[\s.,/|\\%;:]', '', key): value[0] if len(value) == 1 else '' for key, *value in [c.split('=') for c in path_dirs[3].split(';%20')]}  # %20 - это пробел
            except IndexError as err:
                answer = self.make_default_answer_dict(500, f'Incorrect URI structure ("/set_cookie/=/smth" expected)')
                if client.show_errors: answer['msg'] += f'\nServer returned: {err.args[0]}'
            except ValueError as err:
                answer = self.make_default_answer_dict(500, f'Incorrect dividend or divider in requests URI "{request["path"]}"')
                if client.show_errors: answer['msg'] += f'\nServer returned: {err.args[0]}'
            else:
                client.cookie.update(c)
                msg = "".join([f"<p><strong>{key}</strong>: <i>{value}</i></p>" for key, value in c.items()])
                if msg == "":
                    answer = self.make_default_answer_dict(200, '<p>Nothing has been added to the cookie</p>')
                else:
                    answer = self.make_default_answer_dict(200, f'{msg}<p>Has been added to the cookie</p>')
            finally:
                return answer

        answer = ''
        # всяческие проверки и обработка куки-заголовка
        if request is None:
            answer = None
        elif request['method'] not in ['GET', 'POST']:
            answer = self.make_default_answer_dict(501, f'"{request["method"]}" method is not supported. Use GET/POST')
        elif request['version'] != self.http_ver:
            answer = self.make_default_answer_dict(505, f'"{request["version"]}" version is not supported. Use "{self.http_ver}"')
        elif request.get('Cookie'):
            try:
                c = {key: value[0] if len(value) == 1 else True for key, *value in [c.split('=') for c in request['Cookie'].split('; ')]}
            #     ухищрения с value сделаны, чтобы обработать маркеры "Secure" и "HttpOnly"
            except ValueError as err:
                answer = self.make_default_answer_dict(400, 'Incorrect Cookie HTTP-header')  # хотя можно и fatal_error вызывать
                if client.show_errors: answer['msg'] += f'\nServer returned: {err.args[0]}'
            else:
                client.cookie.update(c)

        if answer != '':
            return answer

        get_func_dict = {
            '': get_start_menu,
            'div': divide
        }

        post_func_dict = {
            'short_log': change_log_type,
            'show_errors': change_errors_msgs,
            'set_cookie': set_cookie
        }

        path_dirs = request['path'].split('/')
        if request['method'] == 'GET':
            path_dirs[-1] = path_dirs[-1][:path_dirs[-1].find('?')]
            request['path'] = '/'.join(path_dirs)  # делается для make_log на будущее
            if path_dirs[1] in get_func_dict:
                answer = get_func_dict[path_dirs[1]]()  # я ожидаю, что в path будет хотя бы один "/"

        elif request['method'] == 'POST':
            if path_dirs[1] in post_func_dict:
                answer = post_func_dict[path_dirs[1]]()

        if answer == '':
            answer = self.make_default_answer_dict(404, f'"<i>{"/".join(path_dirs)}</i>" not found at server')

        return answer


    def accept_request(self, client, conn, buff_size=1024):
        '''Принимает запрос клиента и возвращает его в виде словаря.
        В случае ошибки в структуре запроса инициирует fatal_error с соответствующим ответом
        и роняет сервер (так было в тз).
        Если из сокета пришла "" (клиент разорвал соединение), возвращает None.'''

        def accept_raw_request_data():
            raw_data = ''
            while True:
                chunk = conn.recv(buff_size)
                raw_data += chunk.decode()
                if raw_data[-buff_size * 2:].find('\r\n\r\n') != -1 or not chunk:  # именно "-buff_size * 2", вдруг
                    break  # начало разделителя прилетело в предыдущем чанке

            return raw_data

        def make_request_from_raw_data(raw_data):
            def make_requests_headers():
                for st in request_strings[1:]:
                    if not st:  # предпоследний или последний элементы списка (возможно, оба) будут "". В любом случае
                        break  # последний элемент станет телом запроса.

                    try:
                        header, value = st.split(': ')
                    except ValueError:
                        self.fatal_error(client, conn, 400, 'HTTP headers is in incorrect format')
                    else:
                        request[header] = value
                else:  # если не будет ни одного путого элемента, значит структура http некорректна
                    self.fatal_error(client, conn, 400, 'HTTP request is in incorrect format (\\r\\n\\r\\n required)')

            def make_requests_body():
                request['body'] = request_strings[-1]
                if int(request.get('Content-Length', 0)) != len(request_strings[-1]):
                    try:
                        request['Content-Length'] = int(request['Content-Length'])
                    except KeyError:
                        self.fatal_error(client, conn, 400, "Can't read requests body without 'Content-Length' header")
                    except ValueError:
                        self.fatal_error(client, conn, 400, 'Incorrect Content-Length value')

                    received = len(request_strings[-1])  # на случай, если в чанке с разделителем прилетел кусочек тела
                    while received < request['Content-Length']:
                        chunk = conn.recv(buff_size).decode()
                        received += len(chunk)
                        request_strings[-1] += chunk

            if not raw_data:
                return

            request = {}
            request_strings = raw_data.split('\r\n')

            try:  # starter-string
                request['method'], request['path'], request['version'] = request_strings[0].split()
            except ValueError:
                self.fatal_error(client, conn, 400, 'HTTP starter string is in incorrect format')

            make_requests_headers()
            make_requests_body()

            return request

        raw_data = accept_raw_request_data()
        return make_request_from_raw_data(raw_data)


    def main(self, client, conn):
        request = self.accept_request(client, conn)
        answer = self.process_request(client, request)
        self.process_response(client, conn, answer)
        self.make_log(client, request, answer)


    def serve_forever(self):
        self.sock.listen(5)
        while True:
            conn, addr = self.sock.accept()
            addr = addr[0]

            for ip in self.clients:
                if addr == ip:
                    client = self.clients[ip]
                    break
            else:
                client = Client(addr)
                self.clients[addr] = client

            Thread(target=self.main, args=(client, conn)).start()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', '-H', help="Servers ip-address")
    parser.add_argument('--port', '-p', help="Servers port")

    args = parser.parse_args()

    if args.host:
        HOST = args.host
    else:
        _ = socket(AF_INET, SOCK_DGRAM)
        _.connect(("8.8.8.8", 80))
        HOST = _.getsockname()[0]
        _.close()

    PORT = int(args.port) if args.port else 80

    return HOST, PORT


host_port = parse_args()

server = MyBaseHTTPServer(host_port)
server.serve_forever()
