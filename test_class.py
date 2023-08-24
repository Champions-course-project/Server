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

working_dir = '.'
os.chdir(working_dir)

logging.basicConfig(filename='server-log.log', filemode='a',
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
    request_body_raw = ''
    request_body = {}
    random_uuid = ''
    __reader = None
    __StreamReader = None
    request_finished = True
    request_correct = True

    def __init__(self, reader: asyncio.StreamReader):
        self.__StreamReader = reader
        return

    async def _async_init(self):
        """
        Анализирует поступившие заголовки. \n
        НЕ СОСТАВЛЯЕТ ОТВЕТ! \n
        Служит только для их удобного разбиения и дальнейшей работы извне.
        """

        async def __reader():
            error_cnt = 0
            data_list = list[str]()
            while True:
                await asyncio.sleep(0.001)
                data = await self.__StreamReader.read(len(self.__StreamReader._buffer))
                if data == b'':
                    if len(data_list) == 0:
                        error_cnt += 1
                        if error_cnt == 3:
                            break
                        else:
                            yield None
                    else:
                        yield data_list[0]
                        data_list = data_list[1:]
                else:
                    error_cnt = 0
                    temp_data_list = data.decode().split("\r\n")
                    for item in temp_data_list:
                        for item2 in item.split('\n'):
                            data_list.append(item2)
                    yield data_list[0]
                    data_list = data_list[1:]

        self.__reader = __reader
        request_headers = list[str]()
        async for line in self.__reader():
            if line != None:
                request_headers.append(line)
            # while len(request_headers) < 2 or (request_headers[-1] != '\r\n' and request_headers[-1] != '\n' and request_headers[-1] != ''):
            #     line = await self.__reader()
            #     request_headers.append(line)
        self.random_uuid = random.randbytes(16).hex(':', 2)
        logging.info(f"New request: UUID = {self.random_uuid}")
        if len(request_headers) == 0 or (len(request_headers) >= 3 and request_headers[-3] == ''):
            logging.info(
                f"{self.random_uuid} Request unfinished. Terminating session")
            self.request_finished = False
        else:
            try:
                main_line = str(request_headers[0]).replace(
                    "\r\n", "").replace("\n", "").split(' ')
                self.request_type = main_line[0]
                self.request_address = main_line[1]
                try:
                    self.request_http_ver = main_line[2]
                except:
                    self.request_http_ver = 'HTTP/0.9'
            except:
                logging.info(
                    f"{self.random_uuid} Incorrect first line. Terminating session")
                self.request_correct = False
            if self.request_correct:
                data_len = len(request_headers)
                if len(request_headers) > 1 and request_headers[-2] == '':
                    data_len -= 2
                self.request_headers = {request_headers[i].split(
                    ": ")[0]: request_headers[i].split(": ")[1] for i in range(1, data_len)}

                async for line in self.__reader():
                    if line != None:
                        request_headers.append(line)
                if len(request_headers) > 1 and request_headers[-2] == '':
                    try:
                        self.request_body = json.loads(request_headers[-1])
                    except:
                        pass

                logging.info(
                    f"{self.random_uuid} Type: {self.request_type}")
                logging.info(
                    f"{self.random_uuid} Address: {self.request_address}")
                logging.info(
                    f"{self.random_uuid} HTTP version: {self.request_http_ver}")
                logging.info(
                    f"{self.random_uuid} Headers: {self.request_headers}")
                logging.info(
                    f"{self.random_uuid} Request body: {self.request_body}")
        return

    pass


class ResponseCreator:
    __responce_protocol = ''
    __responce_code = 400
    __responce_name = ''
    __responce_headers = list[str]()
    __responce_body = []
    __responce_uuid = ''
    __writer = None

    def __init__(self, writer: asyncio.StreamWriter, responce_uuid: str, responce_protocol: str, responce_code: int | str, responce_name: str, responce_headers: list[str], responce_body: dict = {}):
        self.__responce_uuid = responce_uuid
        self.__responce_protocol = responce_protocol
        self.__responce_code = responce_code
        self.__responce_name = responce_name
        self.__responce_headers = responce_headers
        self.__responce_body = responce_body
        self.__writer = writer
        return

    async def _async_send(self):
        full_structure = []
        full_structure.append(
            f"{self.__responce_protocol} {self.__responce_code} {self.__responce_name}")
        if type(self.__responce_body) in (list, dict):
            try:
                responce_body_str = json.dumps(
                    self.__responce_body, ensure_ascii=False, sort_keys=False)
            except:
                responce_body_str = ''
        else:
            responce_body_str = self.__responce_body
        content_length = len(responce_body_str)
        for header in self.__responce_headers:
            if header.split(":")[0].lower() == "content-length":
                full_structure.append(f"Content-Length: {content_length}")
        full_structure.append('')
        if content_length != 0:
            full_structure.append(responce_body_str)
        full_responce = ('\n'.join(full_structure)).encode()

        full_responce += b'\n'
        logging.info(
            f"{self.__responce_uuid} Sending responce: {full_responce}")
        self.__writer.write(full_responce)
        await self.__writer.drain()
        self.__writer.close()
        return

    pass


def get_from_file(requests_dict: dict):
    """
    Реализует фиктивный запрос на сервер - открывает файл и выдает необходимую информацию.
    """
    with open("data.json", "r", encoding="UTF-8") as IF:
        data = (dict)(json.load(IF))
    logging.debug("Opening a file.")
    ERR = {"error": True}
    requested_info = requests_dict["request"]
    given_args = requests_dict["args"]
    output_dict = {}
    try:
        if 'faculty' == requested_info:
            logging.debug("Request for faculty. Success.")
            output_dict = {'error': False, 'data': (list)(data.keys())}

        elif 'course' == requested_info:
            if "faculty" in given_args:
                logging.debug("Request for course. Success.")
                output_dict = {'error': False, 'data': (
                    list)(data[given_args["faculty"]].keys())}
            else:
                output_dict = ERR
                logging.debug("Request for course. Failure.")

        elif 'group' == requested_info:
            if "faculty" in given_args and "course" in given_args:
                logging.debug("Request for group. Success.")
                output_dict = {'error': False, 'data': (list)(
                    data[given_args["faculty"]][given_args["course"]])}
            else:
                output_dict = ERR
                logging.debug("Request for group. Failure.")

        elif 'students' == requested_info:
            if "faculty" in given_args and "course" in given_args and "group" in given_args:
                logging.debug("Request for students. Success.")
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
                logging.debug("Request for students. Failure.")

        elif 'dates' == requested_info:
            if "faculty" in given_args and "course" in given_args and "group" in given_args:
                logging.debug("Request for dates. Success.")
                dates_list = []
                with open("Dates.txt", "r", encoding="UTF-8") as IF:
                    for line in IF:
                        dates_list.append(line.replace("\n", ""))
                output_dict = {'error': False, 'data': dates_list}
            else:
                output_dict = ERR
                logging.debug("Request for dates. Failure.")

        elif 'statuses' == requested_info:
            if "faculty" in given_args and "course" in given_args and "group" in given_args:
                logging.debug("Request for statuses. Success.")
                with open("statuses.json", "r", encoding="UTF-8") as IF:
                    statuses = (dict)(json.load(IF))
                try:
                    output_dict = {'error': False, 'data': (dict)(
                        statuses[given_args["faculty"]][given_args["course"]][given_args["group"]])}
                except:
                    output_dict = {'error': False, 'data': {}}
            else:
                output_dict = ERR
                logging.debug("Request for statuses. Failure.")

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
    for faculty in statuses_input:
        courses_dict = statuses_input[faculty]
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


async def async_main(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # get request
    incoming_request = RequestAnalyzer(reader)
    await incoming_request._async_init()
    # request recieved, now working with it
    if incoming_request.request_finished:
        uuid = incoming_request.random_uuid
        request_body = incoming_request.request_body
        # TODO: check if request is for table or not
        request_correct = incoming_request.request_correct
        if len(request_body) == 2 and 'type' in request_body and 'data' in request_body and 'args' in request_body['data'] and (request_body['type'] == 'load' and 'request' in request_body['data'] or request_body['type'] == 'save'):
            if request_body['type'] == 'load':
                logging.debug("Type: load, loading now...")
                responce_body = get_from_file(request_body['data'])
            elif request_body['type'] == 'save':
                logging.debug("Type: save, saving now...")
                save_to_file(request_body['data'])
                responce_body = {'error': 0}
            else:
                request_correct = False
        else:
            request_correct = False
        if not request_correct:
            responce_body['error'] = 1
        # sending responce
        responce = ResponseCreator(
            writer, uuid, 'HTTP/1.1', 200, 'OK', ["server: myself", "connection: close"], responce_body)
        await responce._async_send()


async def start_service(host: str, port: int):
    service = await asyncio.start_server(async_main, host, port)
    await service.serve_forever()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default="localhost")
    parser.add_argument('--port', type=int, default=80)

    ConnectionInfoParsed = parser.parse_args()
    HOST = ConnectionInfoParsed.host
    PORT = ConnectionInfoParsed.port

    print(f"Starting tcp server on {HOST}:{PORT}")
    asyncio.run(start_service(HOST, PORT))
    pass


if __name__ == '__main__':
    main()
