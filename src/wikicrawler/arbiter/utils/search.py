import cmd


cli = cmd.Cmd()


def print_results(results, dw=180):
    if isinstance(results[0], dict):
        cli.columnize([f"\t{i}: {r['title']}" for i, r in enumerate(results)], displaywidth=dw)
    elif isinstance(results[0], tuple):
        cli.columnize([f"\t{i}: {r[0]}" for i, r in enumerate(results)], displaywidth=dw)
    else:
        cli.columnize([f"\t{i}: {r}" for i, r in enumerate(results)], displaywidth=dw)
