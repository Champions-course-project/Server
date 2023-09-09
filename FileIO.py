import json
import logging


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
                try:
                    with open("statuses.json", "r", encoding="UTF-8") as IF:
                        statuses = (dict)(json.load(IF))
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
