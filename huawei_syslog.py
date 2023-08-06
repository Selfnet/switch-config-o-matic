import re

from utils import xml_to_keyvalue


def get_time_from_syslog_line(line):
    time_contained = line.split(";")[0]
    time_ = re.match(r"<.*>(.*) HUAWEI", time_contained, re.DOTALL).groups()[0]
    return time_


def parse_syslog_line_userdefined(line):
    msg_text = line.split("; ")[1].split("(")[0]
    return msg_text


def parse_syslog_line_error(line):
    tags = re.findall(r"<error-tag>(.*)</error-tag>", line)
    error_msgs = re.findall(r"<error-message.*>(.*)</error-message>", line)

    return f"ERROR: {tags[0]} | {error_msgs[0]}"


def get_human_readable_syslog_messages(syslog_lines):
    final_messages = []
    for line in syslog_lines:
        if "ssh" in line.lower() and "Body=)" in line:
            continue
        if (
            ("OPS_RESTCONF" in line or "Body=)" in line or "IM_SUPPRESS_LOG" in line)
            and not "<errors>" in line
            and not "ssh" in line.lower()
        ):
            continue
        if "first-time-enable" in line:
            continue
        if "<errors>" in line:
            time_ = get_time_from_syslog_line(line)
            line = f"{time_} | {parse_syslog_line_error(line)}"

        line = re.sub(r"^<\d+>", "", line)
        line = re.sub(r"HUAWEI.*; *", " | ", line, re.DOTALL)
        line = re.sub(r"OPS operation information.", "", line)
        line = re.sub(r"\(UserName=.*Body=", "", line, re.DOTALL)
        line = re.sub(r"\(user=\"_autoconfig.py\", session=\d*\)", "", line)
        line = re.sub(r"(ServiceType=sftp,)|(VPNInstanceName=_public_,)", "", line)
        line = re.sub(r" +", " ", line)

        if "\n" in line:
            line = "; ".join([s.strip() for s in line.splitlines()])
            line = line.replace(":;", ":")

        if "</" in line:
            time_ = line.split("|")[0].strip()
            line = xml_to_keyvalue(line.split("|")[1].strip().replace(")", ""))
            line = f"{time_} | {line}"

        final_messages.append(line)

    return final_messages
