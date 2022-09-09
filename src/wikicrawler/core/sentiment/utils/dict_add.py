def add_dict(a, b, scale_factor=1.0):
    c = {}
    for k, v in a.items():
        c[k] = v*scale_factor + b[k]*(1.0-scale_factor)

    return c