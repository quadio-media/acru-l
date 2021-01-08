import os

from acru_l.core import app_factory


os.environ.setdefault("FOO", "bar")


def run_synth(config_path: str):
    app = app_factory(
        account="fake",
        region="fake",
        config_path=config_path,
        section="tool.acru-l",
        deploy_id="test",
    )
    return app.synth()


def test_network_stack_factory():
    output = run_synth("./tests/fixtures/config/network.toml")
    assert output.get_stack("MyNetwork")


def test_ses_stack_factory():
    output = run_synth("./tests/fixtures/config/ses.toml")
    assert output.get_stack("MyEmails")


def test_lucario_stack_factory():
    output = run_synth("./tests/fixtures/config/lucario.toml")
    assert output.get_stack("DummyDjango")


def test_users_stack_factory():
    output = run_synth("./tests/fixtures/config/users.toml")
    assert output.get_stack("MyUsersService")


def test_certs_stack_factory():
    output = run_synth("./tests/fixtures/config/certs.toml")
    assert output.get_stack("MyCerts")
