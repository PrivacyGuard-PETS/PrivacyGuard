import os
import re

import pandas as pd
import spacy

from Python.utils.miscellaneous import remove_digits_punctuations


def clean_if_rule(item_d) -> dict:
    """
    Clean permissions to get the clean triggers and actions in IFTTT

    Args:
        item_d (dict): each raw trigger or action dict

    Returns:
        result_d (dict): clean trigger or action dict

    """
    result_d: dict = {}
    id_s: str = item_d["id"]
    idx_i: int = id_s.rfind(".")
    state_s: str = id_s[idx_i + 1 :]
    # result_d["id"] = " ".join(split_camel_case(state_s))
    result_d["id"] = state_s
    result_d["name"] = item_d["name"]
    result_d["description"] = item_d["description"]
    result_d["service_slug"] = item_d["service_slug"]
    result_d["service_name"] = item_d["service_name"]
    return result_d


def get_ifttt_json_from_csv(file_name_s: str) -> dict:
    """
    Get IFTTT raw json(without device) from csv

    Args:
        file_name_s (str): csv file name

    Returns:
        result_d (dict): ifttt json

    """

    csv_df: pd.DataFrame = pd.read_csv(file_name_s, index_col=0)

    ifttt_raw_d: dict = {}

    for _, item_df in csv_df.iterrows():
        description_s: str = item_df["description"]
        friendly_id_s: str = item_df["friendly_id"]
        name_s: str = item_df["name"]
        permissions_l: list = eval(item_df["permissions"])
        triggers_raw_l: list = [
            item_d for item_d in permissions_l if item_d["id"].startswith("/triggers")
        ]
        triggers_l: list = [clean_if_rule(item_d) for item_d in triggers_raw_l]

        actions_raw_l: list = [
            item_d for item_d in permissions_l if item_d["id"].startswith("/actions")
        ]
        actions_l: list = [clean_if_rule(item_d) for item_d in actions_raw_l]

        ifttt_raw_d[friendly_id_s] = {
            "description": description_s,
            "friendly_id": friendly_id_s,
            "name": name_s,
            "triggers": triggers_l,
            "actions": actions_l,
        }
    return ifttt_raw_d


# def get_nouns_verbs_from_string(
#     nlp_nlp: spacy.lang.en.English, string_s: str
# ) -> (list, list):
#     """
#     Get nouns and verbs list from a string
#
#     Args:
#         nlp_nlp (spacy.lang.en.English): nlp object
#         string_s (str): string
#
#     Returns:
#         nouns_l (list): all the nouns in the string
#         verbs_l (list): all the verbs in the string
#     """
#
#     string_s = remove_digits_punctuations(string_s)
#
#     nouns_l: list = []
#     verbs_l: list = []
#
#     string_nlp = nlp_nlp(string_s)
#     for token_nlp in string_nlp:
#         if token_nlp.pos_ in ["PROPN", "NOUN"]:
#             nouns_l.append(token_nlp.lemma_)
#         elif token_nlp.pos_ in [
#             "VERB",
#             "MD",
#             "VB",
#             "VBD",
#             "VBG",
#             "VBN",
#             "VBP",
#             "VBZ",
#             "ADP",
#             "IN",
#             "RP",
#         ]:
#             verbs_l.append(token_nlp.lemma_)
#     return nouns_l, verbs_l


def get_nouns_verbs_from_string(noun_dev_d: dict, string_s: str):
    """
    Get nouns and verbs list from a string

    Args:
        noun_dev_d (dict): noun to device dict
        string_s (str): string

    Returns:
        nouns_l (list): all the nouns in the string
        verbs_l (list): all the verbs in the string
    """

    string_s = remove_digits_punctuations(string_s)
    string_l: list = string_s.split()

    nouns_l: list = []
    verbs_l: list = []

    for token_s in string_l:
        if token_s in noun_dev_d:
            nouns_l.append(token_s)
        elif token_s in [
            "on",
            "off",
        ]:
            verbs_l.append(token_s)
    return nouns_l, verbs_l


def get_similar_device_from_nouns(noun_dev_d: dict, noun_s: str) -> str:
    return noun_dev_d[noun_s]


def infer_device_type_from_smartapp(
    nlp_nlp,
    noun_dev_d: dict,
    capa_fix_dev_d: dict,
    capa_def_dev_d: dict,
    capa_s: str,
    input_s: str,
    section_s: str,
    varname_s: str,
    description_s: str,
    filename_s: str,
) -> str:
    """
    Infer device type from smartapp text information

    Args:
        nlp_nlp (spacy.lang.en.English): nlp object
        dev_noun_d (dict):
        capa_dev_d (dict):
        input_s (str):
        section_s (str):
        varname_s (str):
        description_s (str):
        filename_s (str):

    Returns:
        device_s (str): device inferred
    """
    weights_l: list = [1, 1, 0, 0.2, 0.1]
    texts_l: list = [input_s, section_s, varname_s, description_s, filename_s]
    len_texts_i: int = len(texts_l)

    device_s: str = ""

    device_sort_d: dict = {}

    for i_i in range(len_texts_i):
        nouns_l, verbs_l = get_nouns_verbs_from_string(noun_dev_d, texts_l[i_i])
        for noun_s in nouns_l:
            device_s = get_similar_device_from_nouns(noun_dev_d, noun_s)
            if device_s not in device_sort_d:
                device_sort_d[device_s] = 0
            device_sort_d[device_s] += weights_l[i_i]
    if capa_s in capa_fix_dev_d:
        return noun_dev_d[capa_fix_dev_d[capa_s]]

    device_sort_l: list = sorted(
        device_sort_d.items(), key=lambda item: (-item[1], item[0])
    )
    if len(device_sort_l) > 0:
        device_s = device_sort_l[0][0]
    if device_s == "":
        return capa_def_dev_d.get(capa_s, "")
    return device_s


def infer_device_type_from_ifttt(
    nlp_nlp,
    noun_dev_d: dict,
    capa_fix_dev_d: dict,
    capa_def_dev_d: dict,
    capa_s: str,
    input_s: str,
    section_s: str,
    varname_s: str,
    description_s: str,
    filename_s: str,
) -> str:
    """
    Infer device type from smartapp text information

    Args:
        nlp_nlp (spacy.lang.en.English): nlp object
        dev_noun_d (dict):
        capa_dev_d (dict):
        input_s (str):
        section_s (str):
        varname_s (str):
        description_s (str):
        filename_s (str):

    Returns:
        device_s (str): device inferred
    """
    weights_l: list = [1, 1, 0, 0.2, 0.1]
    texts_l: list = [input_s, section_s, varname_s, description_s, filename_s]
    len_texts_i: int = len(texts_l)

    device_s: str = ""

    device_sort_d: dict = {}

    for i_i in range(len_texts_i):
        nouns_l, verbs_l = get_nouns_verbs_from_string(noun_dev_d, texts_l[i_i])
        for noun_s in nouns_l:
            device_s = get_similar_device_from_nouns(noun_dev_d, noun_s)
            if device_s not in device_sort_d:
                device_sort_d[device_s] = 0
            device_sort_d[device_s] += weights_l[i_i]
    if capa_s in capa_fix_dev_d:
        return noun_dev_d[capa_fix_dev_d[capa_s]]

    device_sort_l: list = sorted(
        device_sort_d.items(), key=lambda item: (-item[1], item[0])
    )
    if len(device_sort_l) > 0:
        device_s = device_sort_l[0][0]
    if device_s == "":
        return capa_def_dev_d.get(capa_s, "")
    return device_s


def infer_device_state_from_ifttt(nlp_nlp, verb_noun_d: dict, id_s: str) -> str:
    string_s = remove_digits_punctuations(id_s)
    string_l: list = string_s.split()
    for str_s in string_l:
        if str_s in verb_noun_d:
            return verb_noun_d[str_s]
    return ""


def infer_device_type(
    nlp_nlp,
    noun_dev_d: dict,
    fix_dev_d: dict,
    def_dev_d: dict,
    capa_slug_s: str,
    var1_s: str,
    var2_s: str,
    var3_s: str,
    var4_s: str,
    var5_s: str,
) -> str:
    """
    Infer device type from smartapp text information

    Args:
        nlp_nlp (spacy.lang.en.English): nlp object
        dev_noun_d (dict):
        capa_dev_d (dict):
        var1_s (str):
        var2_s (str):
        var3_s (str):
        var4_s (str):
        var5_s (str):

    Returns:
        device_s (str): device inferred
    """
    weights_l: list = [1, 1, 0, 0.2, 0.1]
    texts_l: list = [var1_s, var2_s, var3_s, var4_s, var5_s]
    len_texts_i: int = len(texts_l)

    device_s: str = ""

    device_sort_d: dict = {}

    for i_i in range(len_texts_i):
        nouns_l, verbs_l = get_nouns_verbs_from_string(noun_dev_d, texts_l[i_i])
        for noun_s in nouns_l:
            device_s = get_similar_device_from_nouns(noun_dev_d, noun_s)
            if device_s not in device_sort_d:
                device_sort_d[device_s] = 0
            device_sort_d[device_s] += weights_l[i_i]
    if capa_slug_s in fix_dev_d:
        return noun_dev_d.get(fix_dev_d[capa_slug_s], fix_dev_d[capa_slug_s])

    device_sort_l: list = sorted(
        device_sort_d.items(), key=lambda item: (-item[1], item[0])
    )
    if len(device_sort_l) > 0:
        device_s = device_sort_l[0][0]
    if device_s == "":
        return def_dev_d.get(capa_slug_s, "")
    return device_s


def infer_device_type_from_openhab(
    nlp_nlp,
    noun_dev_d,
    fix_dev_d,
    def_dev_d,
    icon_s,
    item_s,
    varname_s,
    label_s,
) -> str:

    if icon_s in fix_dev_d:
        return noun_dev_d.get(fix_dev_d[icon_s], fix_dev_d[icon_s])
    if item_s in def_dev_d:
        return noun_dev_d.get(def_dev_d[item_s], def_dev_d[item_s])

    weights_l: list = [1, 1]
    texts_l: list = [varname_s, label_s]
    len_texts_i: int = len(texts_l)

    device_s: str = ""

    device_sort_d: dict = {}

    for i_i in range(len_texts_i):
        nouns_l, verbs_l = get_nouns_verbs_from_string(noun_dev_d, texts_l[i_i])
        for noun_s in nouns_l:
            device_s = get_similar_device_from_nouns(noun_dev_d, noun_s)
            if device_s not in device_sort_d:
                device_sort_d[device_s] = 0
            device_sort_d[device_s] += weights_l[i_i]

    device_sort_l: list = sorted(
        device_sort_d.items(), key=lambda item: (-item[1], item[0])
    )
    if len(device_sort_l) > 0:
        device_s = device_sort_l[0][0]
    return device_s


def split_op_binding(binding_s):
    # <binding_id>:<type_id>:<thing_id>
    equal_idx_i = binding_s.find("=")
    if equal_idx_i == -1:
        return ""
    item_id_s = binding_s[:equal_idx_i].strip()
    binding_s = binding_s[equal_idx_i + 1 :]
    if item_id_s == "channel":
        colon_idx_i = binding_s.find(":")
        item_id_s = binding_s[:colon_idx_i].strip()
    return item_id_s


def is_op_item_line(line):
    keywords_l = [
        "Color",
        "Contact",
        "DateTime",
        "Dimmer",
        "Group",
        "Image",
        "Location",
        "Number",
        "Player",
        "Rollershutter",
        "String",
        "Switch",
    ]
    return any([line.startswith(keyword_s) for keyword_s in keywords_l])


def get_op_item(line_s):
    # itemtype itemname "labeltext [stateformat]" <iconname> (group1, group2, ...) ["tag1", "tag2", ...] {bindingconfig}
    type_s, name_s, label_s, format_s, icon_s = "", "", "", "", ""
    groups_l, tags_l = [], []
    binding_s = ""

    line_l = line_s.split()
    type_s = line_l[0].strip()
    name_s = line_l[1].strip()

    others_s = " ".join(line_l[2:])
    if "{" in others_s:
        idx_head_i = others_s.rfind("{")
        idx_tail_i = others_s.rfind("}")
        binding_s = others_s[idx_head_i + 1 : idx_tail_i]
        binding_s = binding_s.replace(" ", "").replace('"', "").strip()
        others_s = others_s[:idx_head_i]

    if "(" in others_s:
        idx_head_i = others_s.rfind("(")
        idx_tail_i = others_s.rfind(")")

        tmp_groups_l = others_s[idx_head_i + 1 : idx_tail_i].split(",")

        groups_l = [item_s.strip() for item_s in tmp_groups_l]
        others_s = others_s[:idx_head_i]

    if "<" in others_s:
        idx_head_i = others_s.rfind("<")
        idx_tail_i = others_s.rfind(">")
        icon_s = others_s[idx_head_i + 1 : idx_tail_i]
        icon_s = icon_s.strip('"').strip()
        others_s = others_s[:idx_head_i]

    if '"' in others_s:
        idx_head_i = others_s.find('"')
        tmp_s = others_s[idx_head_i + 1 :]
        idx_tail_i = tmp_s.find('"')
        label_s = tmp_s[:idx_tail_i]

        if "[" in label_s:
            fidx_head_i = label_s.rfind("[")
            fidx_tail_i = label_s.rfind("]")
            format_s = label_s[fidx_head_i + 1 : fidx_tail_i].strip()
            label_s = label_s[:fidx_head_i]
        label_s = label_s.strip()

        others_s = others_s[idx_head_i + idx_tail_i :]

    return name_s, [
        type_s,
        label_s,
        format_s,
        icon_s,
        groups_l,
        tags_l,
        binding_s,
    ]


def get_op_triggers(content_s):

    triggers_l = []
    content_s = content_s.replace("\tor", "\n").replace(" or", "\n")
    content_l = content_s.split("\n")
    for line_s in content_l:
        line_s = line_s.strip()

        if len(line_s) == 0:
            continue

        name_s, type_s = "", ""
        command_s = line_s.split()[-1]

        if line_s.startswith("Item"):
            # Item RULEDIMMER received command INCREASE
            # Item switch_living received command
            # Item EQ_Vent received update
            # Item someone_in received update ON
            # Item audio_alarm changed from OFF to ON
            # Item heater changed to ON
            # Item vEQ_Ventilation_Gateway_Reload_ changed to OFF
            # Item sw_Vacation update ON
            pattern = r"\bItem\b[\s\t]+?([\w\W]*?)[\s\n\t]+[received|changed|update]([\w\W]*?)*"
            result = re.search(pattern, line_s)
            type_s = "Item"
            name_s = result.group(1)
        elif line_s.startswith("Member"):
            # Member of gEQ_Ventilation_Mode_End_Date_ changed
            pattern = r"\bMember\b[\s\t]+\bof\b[\s\t]+?([\w\W]*?)[\s\n\t]+[received|changed]([\w\W]*?)*"
            result = re.search(pattern, line_s)
            type_s = "Member"
            name_s = result.group(1)
        elif line_s.startswith("Channel"):
            # Channel 'astro:sun:cad8c2a3:rise#event' triggered START
            # Channel \"astro:sun:home:noon#event\" triggered START
            pattern = r"\bChannel\b[\s\t]+([\w\W]*?)[\s\t]+\btriggered\b([\w\W]*?)"
            result = re.search(pattern, line_s)
            type_s = "Channel"
            name_s = result.group(1)[1:-1]
        elif line_s.startswith("Thing"):
            # Thing \"zwave:device:77c679d29e:node2\" changed
            pattern = r"\bThing\b[\s\t]+([\w\W]*?)[\s\t]+\bchanged\b([\w\W]*?)"
            result = re.search(pattern, line_s)
            type_s = "Thing"
            name_s = result.group(1)[1:-1]
        elif line_s.startswith("Time"):
            # Time cron "0 0/1 * * * ?"
            # print(line_s)
            type_s = "Time"
            name_s = "cron"
            if '"' in line_s:
                quote_beg_i = line_s.find('"')
                quote_end_i = line_s.rfind('"')
                command_s = line_s[quote_beg_i + 1 : quote_end_i]

        elif line_s.startswith("System"):
            # System started
            # System shuts down
            type_s = "System"
            name_s = ""
        else:
            continue
        triggers_l.append([name_s, command_s, type_s])
    return triggers_l


def clean_op_rule(rule_s):

    rule_s = rule_s.replace("val ", "").replace("var ", "")

    emp_words_l = [
        "Thread::",
        "Math::",
        "Double::",
        "Float::",
        "Long::",
        "String::",
        "DateTimeZone::",
        "OnOffType::",
        "NextPreviousType::",
        "PlayPauseType::",
        "Integer::",
        "HSBType::",
        "OpenClosedType::",
        "Minutes::",
        ".intValue()",
        ".longValue()",
        ".toString()",
        ".toLowerCase()",
        ".toDate()",
        ".intValue",
        ".toString",
        ".toLowerCase",
        ".toDate",
        ".doubleValue",
        ".floatValue",
        ".millis",
        ".toUpperCase",
    ]
    for word_s in emp_words_l:
        rule_s = rule_s.replace(word_s, "")

    var_words_l = [
        "String",
        "Number",
        "HSBType",
        "PercentType",
        "Timer",
        "String[]",
        "Double",
        "Integer",
        "Short",
        "SimpleDateFormat",
        "boolean",
        "DateTimeItem",
        "DateTimeType",
        "GenericItem",
        "DecimalType",
        "SwitchItem",
        "GroupItem",
        "double",
        "OnOffType",
        "HistoricItem",
        "ReentrantLock",
        "Period",
        "float",
        "StringType",
        "Boolean",
        "DateTime",
        "QuantityType<Number>",
        "DateTimeZone",
        "int",
        "QuantityType",
        "NumberItem",
        "StringItem",
        "ContactItem",
        "ZonedDateTime",
        "long",
        "RollershutterItem",
        "State",
    ]

    for word_s in var_words_l:
        rule_s = rule_s.replace("as " + word_s, "")

    rules_l = rule_s.split("\n")
    tmp_l = []
    for line_s in rules_l:
        if ("import" in line_s) or (line_s.strip().startswith("//")):
            continue
        tmp_l.append(line_s)
    rule_s = "\n".join(tmp_l)
    return rule_s


def get_openhab_raw_json(dir_s):
    openhab_d = {}
    open_rule_pattern = r"\brule\b[\s\t]+?([\w\W]*?)[\s\n\t]*?\bwhen\b[\s\n\t]*?([\w\W]*?)\bthen\b([\w\W]*?)\bend\b"
    for path_s in os.listdir(dir_s):
        openhab_path_s = f"{dir_s}/{path_s}"
        items_path_s = openhab_path_s + "/" + "items"

        items_d = {}
        for item_files_s in os.listdir(items_path_s):
            if not item_files_s.endswith(".items"):
                continue
            item_path_s = f"{items_path_s}/{item_files_s}"

            with open(item_path_s, "r", encoding="ISO-8859-1") as fitem:
                for line_s in fitem:
                    line_s = line_s.strip()
                    if is_op_item_line(line_s):
                        item_name_s, item_detail_l = get_op_item(line_s)
                        items_d[item_name_s] = item_detail_l

        rules_path_s = f"{openhab_path_s}/rules"
        for rule_files_s in os.listdir(rules_path_s):
            if not rule_files_s.endswith(".rules"):
                continue
            rule_path_s = f"{rules_path_s}/{rule_files_s}"

            with open(rule_path_s, "r", encoding="utf-8") as frule:
                raw_content_s = frule.read()

                first_match = re.search(open_rule_pattern, raw_content_s)

                first_index_i = first_match.span()[0]
                head = raw_content_s[:first_index_i].strip() + "\n"

                regex_content = re.findall(open_rule_pattern, raw_content_s)

                for description_s, triggers_s, rule_s in regex_content:
                    description_s = (
                        description_s.replace('"', "").replace("\n", " ").strip()
                    )

                    if "//" in description_s:
                        tmp_index_i = description_s.index("//")
                        description_s = description_s[:tmp_index_i]

                    triggers_l = get_op_triggers(triggers_s.strip())
                    rule_s = head + rule_s.strip()

                    rule_s = clean_op_rule(rule_s)

                    fname_s = description_s + "@" + rule_files_s + "#" + path_s

                    openhab_d[fname_s] = {
                        "descriptionStr": description_s,
                        "inputMap": items_d,
                        "triggersList": triggers_l,
                        "ruleStr": rule_s,
                    }

    return openhab_d
