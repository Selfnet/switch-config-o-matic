import re

def _get_time_from_syslog_line(line):
    time_contained = line.split(";")[0]
    time_ = re.match(r"<.*>(.*) HUAWEI", time_contained, re.DOTALL).groups()[0]
    return time_

def _parse_syslog_line_userdefined(line):
    msg_text = line.split("; ")[1].split("(")[0]
    return msg_text

def _parse_syslog_line_error(line):
    tags = re.findall(r"<error-tag>(.*)</error-tag>", line)
    error_msgs = re.findall(r"<error-message.*>(.*)</error-message>", line)

    return f"{tags[0]} | {error_msgs[0]}"

def get_errors_from_syslog_lines(lines):
    errors = []
    for line in lines:
        if "<error>" in line:
            try:
                time_ = _get_time_from_syslog_line(line)
                errors.append(f"{time_} | {_parse_syslog_line_error(line)}")
            except:
                errors.append(line)
    
    if len(errors) == 0:
        return ["No errors."]
    
    return errors

def get_infos_from_syslog_lines(lines):
    infos = []
    for line in lines:
        if "OPS_LOG_USERDEFINED_INFORMATION" in line:
            try:
                time_ = _get_time_from_syslog_line(line)
                infos.append(f"{time_} | {_parse_syslog_line_userdefined(line)}")
            except:
                infos.append(line)
    
    if len(infos) == 0:
        return ["No log entries."]
    
    return infos
