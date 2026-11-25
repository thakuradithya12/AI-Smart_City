from scripts.sync_readme_workflow import README, SOURCE, generated_table, synced_readme


def test_readme_workflow_table_matches_generated_workflow_reference():
    readme = README.read_text(encoding="utf-8")
    workflow = SOURCE.read_text(encoding="utf-8")

    assert synced_readme(readme, generated_table(workflow)) == readme
