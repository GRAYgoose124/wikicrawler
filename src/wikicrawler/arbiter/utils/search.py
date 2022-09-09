def print_results(results, precache):
    for idx, res in enumerate(results):
        if isinstance(res, str):
            print(f"\t{idx}: {res}")
        elif 'title' in res and isinstance(res, dict):
            print(f"{idx}: {res['title']}")
        elif not precache: # TODO: Just check if list.
            print(f"{idx}: {res[0]}")
        else:
            print(f"{idx}: {res}")

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
