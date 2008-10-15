def zip_fill(default, *seqs):
    filler = lambda *seq: [el if el is not None else default for el in seq]
    return map(filler, *seqs)
