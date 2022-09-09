import cmd


cli = cmd.Cmd()


def print_results(results, dw=240):
   

    if isinstance(results[0], dict):
        cli.columnize([f"\t{i}: {r['title']}" for i, r in enumerate(results)], displaywidth=dw)
    elif isinstance(results[0], tuple):
        cli.columnize([f"\t{i}: {r[0]}" for i, r in enumerate(results)], displaywidth=dw)
    else:
        cli.columnize([f"\t{i}: {r}" for i, r in enumerate(results)], displaywidth=dw)
        

def select_result(results, precache, index=None):
    if len(results) > 1:
        try:
            if index is None:
                selected = None
                while selected is None:
                    selected = int(input("Choose a result: "))
            else:
                selected = index

            if not precache:
                result = results[selected][1]()
            else:
                result = results[selected]


        except ValueError as e:
            pass
    else:
        result = results[0]

    return result
