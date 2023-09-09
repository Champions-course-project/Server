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

import ConnectionHandler
import FileIO

ERR = {'error': 1}
ALL_METHODS = ('GET', 'POST', 'OPTIONS', 'HEAD', 'PUT',
               'PATCH', 'DELETE', 'TRACE', 'CONNECT')
SUPPORTED_METHODS = ('GET', 'POST', 'OPTIONS', 'HEAD')

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


async def request_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    # get request
    incoming_request = ConnectionHandler.RequestAnalyzer(reader)
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
        responce = ConnectionHandler.Responce_0_9(writer, request_uuid)
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
            responce_body = FileIO.get_from_file(request_body['data'])
        elif request_body['type'] == 'save':
            FileIO.save_to_file(request_body['data'])
            responce_body = {'error': 0}
        else:
            table_request_correct = False
    else:
        table_request_correct = False
    if not table_request_correct:
        responce_body = ERR
    # sending responce
    responce = ConnectionHandler.ResponseCreator(
        writer, request_uuid, 'HTTP/1.1', 200, 'OK', responce_body=responce_body)
    await responce._async_send()


async def start_service(host: str, port: int):
    service = await asyncio.start_server(request_handler, host, port)
    await service.serve_forever()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default="0.0.0.0")
    parser.add_argument('--port', type=int, default=80)

    ConnectionInfoParsed = parser.parse_args()
    HOST = ConnectionInfoParsed.host
    PORT = ConnectionInfoParsed.port

    print(f"Starting tcp server on {HOST}:{PORT}")
    asyncio.run(start_service(HOST, PORT))
    pass


if __name__ == '__main__':
    main()
