from invoke import Collection, task

@task
def test(ctx, coverage=False, flags=""):
    if "--verbose" not in flags.split():
        flags += " --verbose"
    runner = "python"
    if coverage:
        runner = "coverage run --source=state_machine"
    ctx.run("{0} tests/test_state_machine.py {1}".format(runner, flags), pty=True)

@task
def coverage(ctx):
    ctx.run("coverage run --source=state_machine tests/state_machine.py --verbose")

ns = Collection(test, coverage)
