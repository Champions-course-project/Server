import logging
import asyncio
import random
import json

BODY_METHODS = ('POST', 'PUT', 'PATCH')


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
        with open("./secure/html_0_9.html", 'r', encoding='utf-8') as IF:
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
