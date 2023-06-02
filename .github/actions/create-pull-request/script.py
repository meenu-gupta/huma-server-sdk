from typing import Optional

from github import Github, GithubException
from github.Repository import Repository


def read_file(filepath: str) -> list[str]:
    try:
        with open(filepath, "r+") as input_file:
            file_content = input_file.read()
    except FileNotFoundError:
        file_content = ""
    return file_content


def create_new_branch(
    repo: Repository, target_branch: str, source_branch: str, n: Optional[int] = None
) -> str:
    """Create A New Branch

    Args:
        target_branch (str): The name of the new branch
        source_branch (str): The name of the source branch
        repo (Repository): Github Repository Class
        n (Optional[int], optional): automatic branch number to avoid "Branch already exists" error. Defaults to None.

    Returns:
        str: name of new branch
    """

    sb = repo.get_branch(source_branch)
    new_branch = target_branch + f"_{str(n)}" if n else target_branch
    try:
        repo.create_git_ref(ref="refs/heads/" + new_branch, sha=sb.commit.sha)
    except GithubException as e:
        if e.data["message"] == "Reference already exists":
            n = n + 1 if n else 1
            return create_new_branch(repo, target_branch, source_branch, n=n)
        raise e

    return new_branch


def change_exist(
    repo: Repository,
    folder: str,
    old_branch: str,
    new_branch: str,
    file_to_update_path: str,
):

    old_dir_content = repo.get_contents(folder, old_branch)
    new_dir_content = repo.get_contents(folder, new_branch)
    remote_old_sha = next(
        (file.sha for file in old_dir_content if file.path == file_to_update_path), None
    )
    remote_new_sha = next(
        (file.sha for file in new_dir_content if file.path == file_to_update_path), None
    )
    if remote_new_sha == remote_old_sha:
        branch = repo.get_git_ref(f"heads/{new_branch}")
        branch.delete()
        return False
    return True


def commit_changes(
    repo: Repository,
    file_to_update_path: str,
    folder: str,
    source_branch: str,
    commit_message: str,
):
    """Commit new changes

    Args:
        repo (Repository): the reposistory class
        file_to_update_path (str): path to updated file
        folder (str): folder contaning updated file
        source_branch (str): the branch to commit into
        commit_message (str): the commit message

    Raises:
        ValueError
    """

    dir_content = repo.get_contents(folder, source_branch)
    remote_sha = next(
        (file.sha for file in dir_content if file.path == file_to_update_path), None
    )

    if remote_sha is None:
        raise ValueError(f"File not found {file_to_update_path}")

    new_content = read_file(file_to_update_path)

    response = repo.update_file(
        path=file_to_update_path,
        message=commit_message,
        content=new_content,
        sha=remote_sha,
        branch=source_branch,
    )
    return response


if __name__ == "__main__":
    import os

    repository = os.environ["GITHUB_REPOSITORY"]
    repo_token = os.environ["INPUT_TOKEN"]
    target_branch = os.environ["INPUT_BRANCH"]
    source_branch = os.environ["INPUT_BASE"]
    body = os.environ["INPUT_BODY"]
    title = os.environ["INPUT_TITLE"]
    folder_with_changes = os.environ.get("INPUT_FOLDER")
    folder_with_changes = folder_with_changes if folder_with_changes else "."
    file_path = os.environ["INPUT_FILE_PATH"]
    message = os.environ["INPUT_COMMIT_MESSAGE"]

    gh = Github(repo_token)
    remote_repo = gh.get_repo(repository)

    target_branch = create_new_branch(
        repo=remote_repo, target_branch=target_branch, source_branch=source_branch
    )

    commit_changes(
        repo=remote_repo,
        file_to_update_path=file_path,
        folder=folder_with_changes,
        source_branch=target_branch,
        commit_message=message,
    )

    if change_exist(
        repo=remote_repo,
        folder=folder_with_changes,
        old_branch=source_branch,
        new_branch=target_branch,
        file_to_update_path=file_path,
    ):
        remote_repo.create_pull(
            title=title, body=body, base=source_branch, head=target_branch
        )
