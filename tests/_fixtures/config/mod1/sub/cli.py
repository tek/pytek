from tek import cli, Config


@cli(parse_cli=False)
def cli_test():
    return Config['sec1'].key1
