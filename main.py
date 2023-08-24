"""
Этот файл будет использоваться в качестве скрипта для ответов на HTTP-запросы.
"""

import sys
import os

working_dir = '.'
os.chdir(working_dir)

# GLOBAL_FILE = open("log.log", "a", encoding="UTF-8")
if sys.platform == "win32":
    pass
elif sys.platform == "linux":
    pass
else:
    raise TypeError("""
    Current platform is unsupported.
    Supported platforms are Windows and Linux.
    Consider contacting main developer to add implementation.
    """)


def answer_for_request():
    # GLOBAL_FILE.write("Request:\n")
    # get headers from browser
    request_headers = []
    while len(request_headers) < 2 or (request_headers[-1] != '\r\n' and request_headers[-1] != '\n' and request_headers[-1] != ''):
        line = sys.stdin.readline()
        request_headers.append(line)

    if request_headers[-1] == '':
        # GLOBAL_FILE.write("Unfinished request, exiting...\n")
        # GLOBAL_FILE.write(
        #     f"Current headers are: {str(request_headers)}\n\n")
        exit()

    main_line = str(request_headers[0]).replace(
        "\r\n", "").replace("\n", "").split(' ')

    # with open("file.txt", "a", encoding="UTF-8") as RQ:
    #     for line in request_headers:
    #         RQ.write(line)

    request_type = main_line[0]
    request_address = main_line[1]
    request_http_ver = main_line[2]
    # GLOBAL_FILE.write(request_headers[0])
    request_params = {}
    if len(request_address.split("?")) > 1:
        request_params_pairs = request_address.split("?")[1].split("&")
        for pair in request_params_pairs:
            key = pair.split("=")[0]
            value = pair.split("=")[1]
            request_params[key] = value
        request_address = request_address.split("?")[0]

    # prepare answer
    answer_short_code = 404
    answer_long_name = "Not Found"
    answer_data_type = 'file'
    answer_filename = ''
    answer_json_data = {}
    answer_raw_code = ''
    answer_content_type = "text/html"

    answer_primary_headers = []
    answer_additional_headers = []

    # GLOBAL_FILE.write("Preparing for responce...\n")
    # if this request came from application
    if request_type == "POST":
        if request_address == "/table":
            # TODO: проверка авторизации
            authorized = True
            if authorized:
                # TODO: посмотреть тип запроса и выполнить действия в соответствии с ним
                pass
            else:
                # TODO: вернуть 303
                pass
            # TODO: ВСЕГДА указывай Content-Length после приема POST
            answer_additional_headers.append("Content-Length: ")
        else:
            # TODO: если запрос не на table, вернуть 303 с указанием на тот же адрес -> 404
            pass

    # if this is a usual request
    else:
        if request_address == "/":
            # GLOBAL_FILE.write("Sending 303\n")
            answer_short_code = 303
            answer_long_name = "See Other"
            answer_additional_headers.append(
                "Location: http://localhost/index.html")
            answer_data_type = ''
        else:
            try:
                open(working_dir + request_address)
                # GLOBAL_FILE.write("Sending 200\n")
                answer_short_code = 200
                answer_long_name = "OK"
                answer_filename = request_address[1:]
            except:
                # GLOBAL_FILE.write("Sending 404\n")
                answer_short_code = 404
                answer_long_name = "Not Found"
                answer_data_type = 'code'
                answer_raw_code = """
<!DOCTYPE html>
<html>
<head>
<title>404 Not Found</title>
</head>
<body>
<h1>404 Not Found</h1>
</body>
</html>
"""

    # GLOBAL_FILE.write("Writing to a requests_list.txt\n")
    # with open("requests_list.txt", "a", encoding="UTF-8") as OF:
    #     OF.write(request_type + '\n')
    #     OF.write(request_address + '\n')
    #     OF.write(request_http_ver + '\n')
    #     OF.write('\n')

    answer_primary_headers.append(
        f"HTTP/1.1 {answer_short_code} {answer_long_name}")

    if answer_short_code != 303:
        if answer_filename.endswith(".js"):
            answer_content_type = "text/javascript"
        elif answer_filename.endswith(".css"):
            answer_content_type = "text/css"
        elif answer_data_type == 'json':
            answer_content_type = "application/json"
        elif answer_filename.endswith(('.png', '.ico', '.jpg')):
            answer_content_type = "image/image"
        if answer_content_type in ("image/image"):
            answer_primary_headers.append(
                f"Content-Type: {answer_content_type}")
        else:
            answer_primary_headers.append(
                f"Content-Type: {answer_content_type}; charset=UTF-8")
    answer_primary_headers.append("Server: netcat")
    # answer_primary_headers.append("Connection: close")
    # GLOBAL_FILE.write("Sending primary headers\n")
    for header in answer_primary_headers:
        os.system(f'echo {header}>/dev/stdout')

    # GLOBAL_FILE.write("Sending additional headers\n")
    for header in answer_additional_headers:
        os.system(f'echo {header}>/dev/stdout')

    # required empty line
    os.system("echo >/dev/stdout")

    # GLOBAL_FILE.write("Sending data\n")
    # write finally this to output
    if answer_data_type == 'file':
        os.system(f"cat {answer_filename}>/dev/stdout")
    elif answer_data_type == 'json':
        os.system(f"echo {answer_json_data}>/dev/stdout")
    elif answer_data_type == 'code':
        os.system(f"echo '{answer_raw_code}'>/dev/stdout")

    # GLOBAL_FILE.write("Done\n\n")
    os.system("echo >/dev/stdout")


answer_for_request()

# GLOBAL_FILE.close()
exit()
