from pathlib import Path


def test_git_repo_input(tmp_path: Path):
    # Create a temporary git repository
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    # git_command(["init"], cwd=repo_path, capture_output=True)
    # git_command(["config", "user.name", "Test User"], cwd=repo_path)
    # git_command(["config", "user.email", "test@example.com"], cwd=repo_path)
    # (repo_path / "test_file.txt").write_text("hello")
    # git_command(["add", "."], cwd=repo_path, capture_output=True)
    # git_command(["commit", "-m", "initial"], cwd=repo_path, capture_output=True)
    # # Create a tag
    # git_command(["tag", "v1.0"], cwd=repo_path, capture_output=True)


#     # Create a rebuildr file
#     rebuildr_file = tmp_path / "rebuildr.py"
#     rebuildr_file.write_text(
#         f"""
# from rebuildr.descriptor import Descriptor, GitRepoInput, Inputs

# image = Descriptor(
#     inputs=Inputs(
#         external=[
#             GitRepoInput(
#                 url="{repo_path}",
#                 ref="v1.0",
#                 target_path="my-repo",
#             )
#         ]
#     )
# )
# """
#     )

# # Run rebuildr
# with tempfile.TemporaryDirectory() as output_dir:
#     tar_path = Path(output_dir) / "context.tar"
#     with patch.object(
#         sys,
#         "argv",
#         ["rebuildr", "load-py", str(rebuildr_file), "build-tar", str(tar_path)],
#     ):
#         main()

#     assert tar_path.exists()

#     with tarfile.open(tar_path, "r:") as tar:
#         names = tar.getnames()
#         assert "my-repo/test_file.txt" in names
