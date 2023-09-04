"""
Экспериментальный класс для ответов на HTTP-запросы. Возможно использование вместо основного файла.
"""

import sys
import logging
import os
import random
import json
import asyncio
import argparse

ERR = {'error': 1}
ALL_METHODS = ('GET', 'POST', 'OPTIONS', 'HEAD', 'PUT',
               'PATCH', 'DELETE', 'TRACE', 'CONNECT')
SUPPORTED_METHODS = ('GET', 'POST', 'OPTIONS', 'HEAD')
BODY_METHODS = ('POST', 'PUT', 'PATCH')

working_dir = '.'
os.chdir(working_dir)

logging.basicConfig(filename='server-log.log', filemode='a', encoding='utf-8',
                    level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

if sys.platform == "win32":
    # raise NotImplementedError("Windows is not currently supported.")
    pass
elif sys.platform == "linux":
    pass
else:
    raise TypeError("""
    Current platform is unsupported.
    Supported platforms are Windows and Linux.
    Consider contacting main developer to add implementation.
    """)


class CheckAuth:
    @staticmethod
    def check_cookie(cookie: str):
        raise NotImplementedError()
        return False

    @staticmethod
    def set_cookie(login: str, password: str):
        raise NotImplementedError()
        return '00001111222233334444555566667777'


class RequestAnalyzer:
    request_headers = dict[str, str]()
    request_type = ''
    request_address = ''
    request_http_ver = ''
    request_body = {}
    connection_UUID = ''
    http_0_9 = False
    __line_reader = None
    __StreamReader_wipe = None
    __read_n_bytes = None
    __StreamReader = None
    request_finished = True
    request_correct = True

    def __init__(self, reader: asyncio.StreamReader):
        self.__StreamReader = reader

        async def __lines_reader():
            while True:
                data = await self.__StreamReader.readline()
                if data == b'':
                    self.request_finished = False
                    break
                data = data.decode().replace('\r\n', '').replace('\n', '')
                yield data

        self.__line_reader = __lines_reader

        async def __StreamReader_wipe():
            await self.__StreamReader.read(len(self.__StreamReader._buffer))
            return

        self.__StreamReader_wipe = __StreamReader_wipe

        async def __read_n_bytes(n: int):
            data = b''
            while len(data) < n:
                partial_data = await self.__StreamReader.readline()
                if partial_data == b'':
                    self.request_finished = False
                    return
                data += partial_data
            return data[:n].decode()

        self.__read_n_bytes = __read_n_bytes

        self.connection_UUID = random.randbytes(16).hex(':', 2)
        logging.info(f"New connection: UUID = {self.connection_UUID}")

        return

    async def read_request(self):
        """
        Анализирует поступившие заголовки. \n
        НЕ СОСТАВЛЯЕТ ОТВЕТ! \n
        Служит только для их удобного разбиения и дальнейшей работы извне.
        """
        request_UUID = self.connection_UUID + \
            '::' + random.randbytes(4).hex(':', 2)
        logging.info(f"New request: UUID = {request_UUID}")
        request_headers = list[str]()
        # Step 1. Read all headers, first line included
        async for line in self.__line_reader():
            if line == '':
                if len(request_headers) == 0:
                    continue
                break
            request_headers.append(line)
            if len(request_headers) == 1 and len(line.split(' ')) == 2 and line.split(' ')[0] == 'GET':
                self.http_0_9 = True
                logging.info(
                    f"{request_UUID} HTTP version: HTTP/0.9")
                logging.info(
                    f"{request_UUID} Address: {line.split(' ')[1]}")
                return request_UUID

        # Step 2. Check if first part of request was finished in the first place (e.g. connection wasn't closed)
        if not self.request_finished:
            logging.info(
                f"{request_UUID} Request unfinished. Terminating session")
            return request_UUID
        # Step 3. Get first line of the request
        try:
            main_line = request_headers[0].split(' ')
            self.request_type = main_line[0]
            self.request_address = main_line[1]
            self.request_http_ver = main_line[2]
        except:
            logging.info(
                f"{request_UUID} Incorrect first line. Terminating session")
            self.request_correct = False
            return request_UUID
        # Step 4. Separate headers. Invalid headers are ignored
        for i in range(1, len(request_headers)):
            try:
                __request_splitted = request_headers[i].split(': ')
                __header_name = __request_splitted[0].lower()
                __header_value = __request_splitted[1]
                for p in range(2, len(__request_splitted)):
                    __header_value += __request_splitted[p]
                self.request_headers[__header_name] = __header_value.lower()
            except:
                pass

        # Step 5. Check if we should contain request body. If yes, get it
        if self.request_type in BODY_METHODS:
            if 'content-length' in self.request_headers:
                try:
                    n = int(self.request_headers['content-length'])
                    if n != 0:
                        data = await self.__read_n_bytes(n)
                        if not self.request_finished:
                            logging.info(
                                f"{request_UUID} Request terminated while body being requested. Terminating session")
                            return request_UUID
                        self.request_body = dict(json.loads(data))
                except:
                    logging.info(
                        f"{request_UUID} Invalid content-length header or request body. Terminating session")
                    self.request_correct = False
                    return request_UUID
        # Step 6. Wipe all remaining data in case of re-use of this connection
        await self.__StreamReader_wipe()

        logging.info(
            f"{request_UUID} Type: {self.request_type}")
        logging.info(
            f"{request_UUID} Address: {self.request_address}")
        logging.info(
            f"{request_UUID} HTTP version: {self.request_http_ver}")
        logging.info(
            f"{request_UUID} Headers: {self.request_headers}")
        logging.info(
            f"{request_UUID} Request body: {self.request_body}")
        return request_UUID

    pass


class ResponseCreator:
    __responce_protocol = ''
    __responce_code = 400
    __responce_name = ''
    __responce_headers = {}
    __responce_body = {}
    __responce_uuid = ''
    __writer = None
    __necessary_headers = {
        "server": "denied"
    }
    __additional_headers = {
        "connection": 'close'
    }

    def __init__(self, writer: asyncio.StreamWriter, responce_uuid: str, responce_protocol: str, responce_code: int, responce_name: str, responce_headers: dict[str, str] = {}, responce_body:  str = ''):
        self.__responce_uuid = responce_uuid
        self.__responce_protocol = responce_protocol
        self.__responce_code = responce_code
        self.__responce_name = responce_name
        self.__responce_headers = responce_headers
        self.__responce_body = responce_body
        self.__writer = writer
        return

    async def _async_send(self):
        # preparing responce
        full_structure = []
        # Step 1. First line of responce
        full_structure.append(
            f"{self.__responce_protocol} {self.__responce_code} {self.__responce_name}")

        # Step 2. Prepare responce body for the content-length header
        if type(self.__responce_body) in (list, dict):
            try:
                responce_body_str = json.dumps(
                    self.__responce_body, ensure_ascii=False, sort_keys=False)
            except:
                responce_body_str = self.__responce_body
        else:
            responce_body_str = self.__responce_body
        content_length = len(responce_body_str.encode())

        # Step 3. Convert incoming headers to a dict, if they are still in list form
        if type(self.__responce_headers) == list:
            responce_headers = {header.split(': ')[0].lower(): header.split(': ')[
                1].lower() for header in self.__responce_headers}
        else:
            responce_headers = {header.lower(): self.__responce_headers[header].lower(
            ) for header in self.__responce_headers}

        # Step 4. Add necessary headers: they should be in every responce and their values are strict
        for header in self.__necessary_headers:
            full_structure.append(
                f"{header}: {self.__necessary_headers[header]}")
        full_structure.append(f"content-length: {content_length}")

        # Step 5. Add responce headers
        for header in responce_headers:
            if header not in self.__necessary_headers and header != 'content-length':
                full_structure.append(f"{header}: {responce_headers[header]}")

        # Step 6. Add additional headers: these headers should be in responce, but also can vary: if they were missing, using default values
        for header in self.__additional_headers:
            if header not in responce_headers:
                full_structure.append(
                    f"{header}: {self.__additional_headers[header]}")

        # Step 7. Add empty line after headers
        full_structure.append('')

        # Step 8.
        # if content-length is not 0 or TODO: put, head and other methods which do not require body:
        # add body to the responce
        if content_length != 0:
            full_structure.append(responce_body_str)

        # Step 9. Convert the list to the string
        text_full_responce = '\n'.join(full_structure)

        # Step 10. Encode responce
        full_responce = text_full_responce.encode()
        # LF for correct reading
        full_responce += b'\n'

        # Step 11. Send the responce
        logging.info(
            f"{self.__responce_uuid} Sending responce.")
        self.__writer.write(full_responce)
        await self.__writer.drain()
        self.__writer.close()
        return

    pass


class Responce_0_9:
    """
    Специальный класс для ответа на запросы протокола HTTP/0.9.\n
    Ответ состоит исключительно из страницы "Протокол не поддерживается",
    так как для успешной работы с журналом требуется наличие метода POST (появился в HTTP/1.0)
    """
    __html_code = ''
    __responce_uuid = ''
    __writer = None

    def __init__(self, writer: asyncio.StreamWriter, responce_uuid: str):
        with open("html_0_9.html", 'r', encoding='utf-8') as IF:
            self.__html_code = IF.read()
        self.__responce_uuid = responce_uuid
        self.__writer = writer

    async def _async_send(self):
        logging.info(
            f"{self.__responce_uuid} HTTP/0.9 Sending responce")
        full_responce = self.__html_code.encode()
        self.__writer.write(full_responce)
        await self.__writer.drain()
        self.__writer.close()
        return


def get_from_file(requests_dict: dict):
    """
    Реализует фиктивный запрос на сервер - открывает файл и выдает необходимую информацию.
    """
    with open("data.json", "r", encoding="UTF-8") as IF:
        data = (dict)(json.load(IF))
    ERR = {"error": True}
    requested_info = requests_dict["request"]
    given_args = requests_dict["args"]
    output_dict = {}
    try:
        if 'faculty' == requested_info:
            output_dict = {'error': False, 'data': (list)(data.keys())}

        elif 'course' == requested_info:
            if "faculty" in given_args:
                output_dict = {'error': False, 'data': (
                    list)(data[given_args["faculty"]].keys())}
            else:
                output_dict = ERR

        elif 'group' == requested_info:
            if "faculty" in given_args and "course" in given_args:
                output_dict = {'error': False, 'data': (list)(
                    data[given_args["faculty"]][given_args["course"]])}
            else:
                output_dict = ERR

        elif 'students' == requested_info:
            if "faculty" in given_args and "course" in given_args and "group" in given_args:
                with open("students_list.json", "r", encoding="UTF-8") as IF:
                    students_data = (dict)(json.load(IF))
                try:
                    students_list = (list)(
                        students_data[given_args["group"]])
                except:
                    students_list = []
                output_dict = {'error': False, 'data': students_list}
            else:
                output_dict = ERR

        elif 'dates' == requested_info:
            if "faculty" in given_args and "course" in given_args and "group" in given_args:
                dates_list = []
                with open("Dates.txt", "r", encoding="UTF-8") as IF:
                    for line in IF:
                        dates_list.append(line.replace("\n", ""))
                output_dict = {'error': False, 'data': dates_list}
            else:
                output_dict = ERR

        elif 'statuses' == requested_info:
            if "faculty" in given_args and "course" in given_args and "group" in given_args:
                with open("statuses.json", "r", encoding="UTF-8") as IF:
                    statuses = (dict)(json.load(IF))
                try:
                    output_dict = {'error': False, 'data': (dict)(
                        statuses[given_args["faculty"]][given_args["course"]][given_args["group"]])}
                except:
                    output_dict = {'error': False, 'data': {}}
            else:
                output_dict = ERR

    except Exception as exc:
        output_dict = ERR
        logging.warning("Uncaught exception:", exc_info=True)

    return output_dict


def save_to_file(statuses_input: dict):
    """
    Реализует фиктивный запрос на сервер - открывает файл и сохраняет новую информацию.
    """
    try:
        with open("statuses.json", "r", encoding="UTF-8") as IF:
            file_statuses = (dict)(json.load(IF))
    except:
        file_statuses = {}
    # структура словаря: словарь[faculty_name][course_name][
    # group_name][date_choose][student_choose]: status
    faculty_dict = statuses_input['args']
    for faculty in faculty_dict:
        courses_dict = faculty_dict[faculty]
        for course in courses_dict:
            groups_dict = courses_dict[course]
            for group in groups_dict:
                dates_dict = groups_dict[group]
                for date in dates_dict:
                    students_dict = dates_dict[date]
                    for student in students_dict:
                        status = students_dict[student]
                        if status != "":
                            try:
                                file_statuses[faculty]
                            except:
                                file_statuses[faculty] = {}
                            try:
                                file_statuses[faculty][course]
                            except:
                                file_statuses[faculty][course] = {}
                            try:
                                file_statuses[faculty][course][group]
                            except:
                                file_statuses[faculty][course][group] = {}
                            try:
                                file_statuses[faculty][course][group][date]
                            except:
                                file_statuses[faculty][course][group][date] = {}
                            file_statuses[faculty][course][group][date][student] = status
                        else:
                            try:
                                file_statuses[faculty][course][group][date].pop(
                                    student)
                            except:
                                pass
    with open("statuses.json", "w", encoding="UTF-8") as OF:
        json.dump(file_statuses, OF, ensure_ascii=False,
                  indent=4, sort_keys=True)
    return 200


async def request_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # get request
    incoming_request = RequestAnalyzer(reader)
    request_uuid = await incoming_request.read_request()
    # request recieved, now working with it:
    # 1. If request wasn't finished in the first place:
    if not incoming_request.request_finished:
        return

    # 2. If request was finished, but wasn't correct (e.g. first line incorrect or missing important headers)
    if not incoming_request.request_correct:
        # TODO: HTTP 400 'Bad Request' and default page
        pass

    # 3. If request is HTTP/0.9 for some stupid reason:
    if incoming_request.http_0_9:
        responce = Responce_0_9(writer, request_uuid)
        await responce._async_send()
        return

    # finally, nothing holds me from reading all of the data
    request_address = incoming_request.request_address
    request_http_ver = incoming_request.request_http_ver
    request_type = incoming_request.request_type
    request_body = incoming_request.request_body
    request_headers = incoming_request.request_headers
    request_correct = incoming_request.request_correct

    # check request type
    if request_type in ('GET', 'HEAD'):
        # do usual stuff
        if request_type == 'HEAD':
            # stop here, we need only headers
            pass
        else:
            # continue here, we also require a body
            pass
    elif request_type == 'POST':
        pass
    elif request_type == 'OPTIONS':
        pass
    else:
        pass
    table_request_correct = True
    # TODO: check if request is for table or not
    if len(request_body) == 2 and 'type' in request_body and 'data' in request_body and 'args' in request_body['data'] and (request_body['type'] == 'load' and 'request' in request_body['data'] or request_body['type'] == 'save'):
        if request_body['type'] == 'load':
            responce_body = get_from_file(request_body['data'])
        elif request_body['type'] == 'save':
            save_to_file(request_body['data'])
            responce_body = {'error': 0}
        else:
            table_request_correct = False
    else:
        table_request_correct = False
    if not table_request_correct:
        responce_body = ERR
    # sending responce
    responce = ResponseCreator(
        writer, request_uuid, 'HTTP/1.1', 200, 'OK', responce_body=responce_body)
    await responce._async_send()


async def start_service(host: str, port: int):
    service = await asyncio.start_server(request_handler, host, port)
    await service.serve_forever()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default="127.0.0.1")
    parser.add_argument('--port', type=int, default=80)

    ConnectionInfoParsed = parser.parse_args()
    HOST = ConnectionInfoParsed.host
    PORT = ConnectionInfoParsed.port

    print(f"Starting tcp server on {HOST}:{PORT}")
    asyncio.run(start_service(HOST, PORT))
    pass


if __name__ == '__main__':
    main()
