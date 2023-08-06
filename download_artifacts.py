import argparse
import urllib.parse
import os
from requests import Session


class Gitlab:
    def __init__(self, base_url: str, token: str):
        self.baseurl = base_url
        self.session = Session()
        self.session.headers = {
            "PRIVATE-TOKEN": token,
        }

    def get(self, endpoint: str, params={}, json=True):
        res = self.session.get(f"{self.baseurl}/api/v4/{endpoint}", params=params)
        if json:
            return res.json()
        return res


def download_artifacts(
    project: str | int, branch_name: str, job_name: str, output: str, token: str
):
    encoded_project = urllib.parse.quote(str(project), safe="")
    gitlab = Gitlab("https://git.selfnet.de", token)
    last_scheduled_pipelines = gitlab.get(
        f"projects/{encoded_project}/pipelines",
        params={
            "pagination": "keyset",
            "per_page": 1,
            "order_by": "id",
            "sort": "desc",
            "ref": branch_name,
        },
    )
    if len(last_scheduled_pipelines) == 0:
        raise Exception("No pipelines have been run for specified schedule")
    last_pipeline_id = last_scheduled_pipelines[0]["id"]
    jobs = gitlab.get(f"projects/{encoded_project}/pipelines/{last_pipeline_id}/jobs")

    try:
        build_job = next(job for job in jobs if job["name"] == job_name)
    except StopIteration:
        raise Exception(f"Cannot find job with name {job_name}")

    artifacts = gitlab.get(
        f"projects/{encoded_project}/jobs/{build_job['id']}/artifacts", json=False
    )
    with open(output, "wb") as f:
        for chunk in artifacts.iter_content(chunk_size=8192):
            f.write(chunk)


def main():
    parser = argparse.ArgumentParser(
        prog="Gitlab Artifact Downloader",
        description="Download artifacts from scheduled jobs",
    )
    parser.add_argument(
        "--token", required=True, help="GitLab Access Token (requires API read access)"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=os.path.abspath,
        default="artifacts.zip",
        help="Output filename of the artifacts zip file",
    )
    args = parser.parse_args()
    download_artifacts(
        project="support/siam",
        branch_name="main",
        job_name="build_switch_configs_huawei",
        output=args.output,
        token=args.token,
    )


if __name__ == "__main__":
    main()
