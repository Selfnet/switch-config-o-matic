import db
import dateparser
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--since", help="""Only print switches finished since this date
and unfinished ones. Supports human language.""")
args = parser.parse_args()

if args.since:
    since = dateparser.parse(args.since)
else:
    since = datetime.datetime.min

if __name__ == "__main__":
    print("Switch name | Status | Final IP")
    with db.Session() as session:
        switches = session.query(db.Switch).all()
        for sw in switches:
            if sw.finished_date is None or sw.finished_date > since:
                print(f"{sw.name} | {sw.status.name} | {sw.final_ip}")
