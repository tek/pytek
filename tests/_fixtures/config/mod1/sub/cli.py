from tek import cli, Config


@cli(parse_cli=False)
def cli_test(data):
    data.append(Config['sec1'].key1)
