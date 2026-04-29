def test_config_loads(rails):
    assert rails is not None

def test_config_directory_exists(project_root):
    assert (project_root / "config" / "config.yml").exists()
    assert (project_root / "config" / "input.co").exists()
    assert (project_root / "config" / "output.co").exists()
