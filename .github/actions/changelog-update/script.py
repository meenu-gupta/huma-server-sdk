import errno
import copy
import json
import logging
import os
import re
import sys
from typing import Any

"""
This script allows you to parse the Pull Requests from github and compare it with your CHANGELOG file.
It then updates the existing changelogs with the parseed Pull Request.

@prerequisites:
- All PRs should be listed under the currently ongoing milestones.
- Milestone name should match project version semantic rules. Example of milestone naming: 1.14.34
- PR name should contain ticket name in square brackets to be properly linked to JIRA board. Example of PR name:  [DEV 3445] Changed cool stuff on this PR
- To properly define the group of the PR, labels listed above should be used.

"""

logger = logging.getLogger(__name__)


def get_release_content(pr_list: list[dict[str, str]], name: str) -> list[str]:
    if not pr_list or not name:
        logger.info(f"No release or name, provided")
        return []

    release_content = [f"## [{name}]\n\n"]

    label_object = {"bugs": [], "enhancement": [], "refactoring": [], "changes": []}

    for pr in pr_list:
        pr_labels = [label["name"] for label in pr["labels"]]
        if "NoChangeLog" in pr_labels:
            continue

        change_line = create_change_line(pr)
        if not change_line:
            continue

        if "bug-fix" in pr_labels:
            label_object["bugs"].append(change_line)

        elif "enhancement" in pr_labels:
            label_object["enhancement"].append(change_line)

        elif "refactoring" in pr_labels:
            label_object["refactoring"].append(change_line)

        else:
            label_object["changes"].append(change_line)

    bug_section = []
    if label_object["bugs"]:
        bugs_lines = label_object["bugs"]
        bug_section = ["#### Bugs:\n\n"] + bugs_lines + ["\n"]

    enhancement_section = []
    if label_object["enhancement"]:
        enhancements_lines = label_object["enhancement"]
        enhancement_section = ["#### Enhancements:\n\n"] + enhancements_lines + ["\n"]

    refactor_section = []
    if label_object["refactoring"]:
        refactors_lines = label_object["refactoring"]
        refactor_section = ["#### Refactors:\n\n"] + refactors_lines + ["\n"]

    change_section = []
    if label_object["changes"]:
        changes_lines = label_object["changes"]
        change_section = ["#### Changes:\n\n"] + changes_lines + ["\n"]

    release_content += (
        bug_section + enhancement_section + refactor_section + change_section
    )
    return release_content


def create_change_line(pr: dict[str, Any]) -> str:
    pr_title = pr["title"].strip()
    title_regex = re.compile(r"\[.+?\]")
    ticket_match = title_regex.match(pr_title)  # Search for Ticket Id
    if not ticket_match:
        logger.info("PR title not in appropriate format")
        return
    ticket_enclosed = ticket_match.group()  # Search for Ticket Id
    ticket = ticket_enclosed[1:-1]  # Take out the square bracket
    ticket_url = f"[{ticket}](https://medopadteam.atlassian.net/browse/{ticket})"
    pr_title = pr_title.replace(ticket_enclosed, ticket_url)
    mergedAt: str = pr["mergedAt"]
    date, time = mergedAt.replace("Z", "").split("T")

    return f'- {pr_title} `by {pr["author"]["login"]}` [{date} {time}]\n'


def read_changelogs(filepath: str) -> list[str]:
    try:
        with open(filepath, "r+") as input_file:
            file_changelogs = input_file.readlines()
    except FileNotFoundError:
        file_changelogs = []
    return file_changelogs


def write_changelogs(filepath: str, change_logs_list: list):
    with open(filepath, "w+") as input_file:
        input_file.writelines(change_logs_list)


def update_or_create_changelog(
    content_list: list[str], release_name: str, release_content: list[str]
):
    bold_release_name = f"## [{release_name}]\n"
    # Check if release exist in the previous changelog
    found = [i for i, e in enumerate(content_list) if e == bold_release_name]
    lower_lines = []
    high_lines = []
    if found:
        # Release present in previous Changelogs
        existing_release_index = found[0]
        high_lines = content_list[:existing_release_index]
        prev_releases = content_list[existing_release_index + 1 :]
        pattern = re.compile(r"(##\s\[[\d.]+\])")

        # Look for the end of the old release
        result = (i for i, e in enumerate(prev_releases) if pattern.match(e))
        try:
            next_release_index = next(result)
        except StopIteration:
            next_release_index = None
        if next_release_index:
            # Found a previous release
            # Cut out this point till the end of the file
            lower_lines = prev_releases[next_release_index:]
        else:
            # There are no other releases, so the lower part is empty
            lower_lines = []

    else:
        # Release not present in previous Changelog
        new_release_lines = len(content_list)
        if new_release_lines < 2:
            # Meaning it is just the title "Changelog" that is present
            high_lines = content_list + (["\n"])
        elif new_release_lines == 2:
            # This would mean that the title and an extra line exist
            high_lines = copy.deepcopy(content_list)
        else:
            # There exist other release or at least entries so place new release
            # at the top just after the title
            high_lines = content_list[:2]
            lower_lines = content_list[2:]

    change_log_lines = high_lines + release_content + lower_lines
    return change_log_lines


if __name__ == "__main__":

    release_name = os.environ["INPUT_VERSION"]
    release_json = json.loads(os.environ["INPUT_RELEASE"])

    changelog_path = "./CHANGELOG.md"

    # Parse Pull Request Json into List
    release_content = get_release_content(release_json, release_name)

    # Read Existing Existing Changelogs and Parse it into a list of strings
    existing_changelogs = read_changelogs(filepath=changelog_path)

    if existing_changelogs:
        if existing_changelogs[0] != "# Changelog\n":
            logger.info("File doesn't seem like a change log")
            sys.exit(code=errno.ECANCELED)
        if len(existing_changelogs) < 2 or existing_changelogs[1] != "\n":
            existing_changelogs.insert(1, "\n")
    else:
        existing_changelogs = ["# Changelog\n", "\n"]

    # Create new chnagelog list
    new_changelog_list = update_or_create_changelog(
        content_list=existing_changelogs,
        release_name=release_name,
        release_content=release_content,
    )
    write_changelogs(filepath=changelog_path, change_logs_list=new_changelog_list)
