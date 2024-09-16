import json
import os
import re
import resource


def write_json(file_name_s: str, to_write_ld):
    """
    Write to json file from list or dict

    Args:
        file_name_s (str): json filename
        to_write_ld (list|dict): list or dict which is written to json

    Returns:
        None

    """
    json_s: str = json.dumps(to_write_ld, indent=4)
    with open(file_name_s, "w", encoding="ISO-8859-1") as fpw_fp:
        fpw_fp.write(json_s)


def read_json(file_name_s: str):
    """
    Read to list or dict from json file

    Args:
        file_name_s (str): json filename

    Returns:
        list or dict from the json file

    """
    from_read_ld = {}
    with open(file_name_s, encoding="ISO-8859-1") as fpr_fp:
        from_read_ld = json.load(fpr_fp)
    return from_read_ld

def make_dir(dir_s: str):
    """
    Make directory from directory name, if the directory exists, return

    Args:
        dir_s (str): name of directory

    Returns:
        None

    """
    if os.path.exists(dir_s):
        return
    os.makedirs(dir_s)

def flatten(to_flat_l):
    """
    Expand all the list recursively,
    For exampe: [[],[1,2,3], [4,5,[2,2,6]], [7,[[2,[3]]]], [8,9]] ->
                [1, 2, 3, 4, 5, 2, 2, 6, 7, 2, 3, 8, 9]

    Args:
        to_flat_l (list): List of lists or numbers

    Returns:
        A list with level 1

    """
    to_flat_l = list(to_flat_l)

    if len(to_flat_l) == 0:
        return to_flat_l
    if isinstance(to_flat_l[0], list):
        return flatten(to_flat_l[0]) + flatten(to_flat_l[1:])
    return to_flat_l[:1] + flatten(to_flat_l[1:])


def remove_digits_punctuations(string_s: str) -> str:
    """
    Remove digits and punctuations from string

    Args:
        string_s (str): string

    Returns:
        string_s (str): string removed all the digits and punctuations

    >>> remove_digits_punctuations("Test,[1] Test1")
    """
    string_s = str(string_s)
    string_s = re.sub(r"\d", " ", string_s)
    string_s = re.sub(r"[^\w\s]", " ", string_s)
    string_l: list = string_s.split()

    result_l: list = []
    for item_s in string_l:
        result_l.extend(split_camel_case(item_s))
    string_s = " ".join(result_l)
    return string_s


def split_camel_case(camel_s: str) -> list:
    """
    Split the camel cases into list, e.g., file_Name_String -> ["file", "name", "string"], fileName -> ["file", "name"]

    Args:
        camel_s (str): camel case string

    Returns:
        result_l (list): list of camel cases string

    >>> split_camel_case("file_Name_String")
    ['file', 'name', 'string']
    >>> split_camel_case("fileName")
    ['file', 'name']
    """
    result_l: list = []

    camel_s = re.sub(r"\d", " ", camel_s)
    camel_s = re.sub(r"[^\w\s]", " ", camel_s)
    camel_s = camel_s.replace("TV", "Tv")
    camel_s = camel_s.replace("PC", "Pc")
    camel_s = camel_s.replace("_", " ")
    camels_l: list = camel_s.split()
    for substr_s in camels_l:
        size_i: int = len(substr_s)
        last_i: int = 0
        for i_i in range(size_i):
            if substr_s[i_i].isupper():
                curr_i = i_i
                if substr_s[last_i:curr_i]:
                    result_l.append(substr_s[last_i:curr_i].lower())
                last_i = curr_i
        result_l.append(substr_s[last_i:].lower())
    return result_l


def convert_key_str_value_of_dict(dict_d: dict, type_s: str = "str") -> dict:
    """Convert Key-Value of a dict to Value-Key. If type is list, then value:[keys]; else value:key

    Args:
        dict1 (dict): TODO
        dict2 (dict): TODO

    Returns:
        TODO

    """
    result_d: dict = {}
    for key_s, value_s in dict_d.items():
        if type_s == "list":
            if value_s not in result_d:
                result_d[value_s] = []
            result_d[value_s].append(key_s)
        else:
            result_d[value_s] = key_s
    return result_d


def convert_key_list_value_of_dict(dict_d: dict, type_s: str = "str") -> dict:
    """Convert Key-Value of a dict to Value-Key. If type is list, then value:[keys]; else value:key

    Args:
        dict1 (dict): TODO
        dict2 (dict): TODO

    Returns:
        TODO

    """
    result_d: dict = {}
    for key_s, value_l in dict_d.items():
        for value_s in value_l:
            if type_s == "list":
                if value_s not in result_d:
                    result_d[value_s] = []
                result_d[value_s].append(key_s)
            else:
                result_d[value_s] = key_s
    return result_d


def print_seconds_to_readable(total_i):
    hours_i = total_i // 3600
    minutes_i = (total_i % 3600) // 60
    seconds_i = total_i % 60
    print(f"Time cost: ", end="")
    if hours_i > 0:
        print(f"{hours_i} Hours, ", end="")
    if minutes_i > 0:
        print(f"{minutes_i} Minutes, ", end="")
    print(f"{seconds_i} Seconds.")
    # if seconds_i > 0:
    #     print(f"{seconds_i} Seconds.")
    # elif hours_i == 0 and minutes_i == 0:
    #     print(f"{total_i*1000} Milliseconds.")


def print_memory_usage():
    memory_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    memory_usage_mb = memory_usage_kb / 1024
    print(f"Memory usage: {memory_usage_mb:.2f} MB")
