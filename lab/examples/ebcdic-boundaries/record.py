"""Decode only the text field of one synthetic fixed-length record."""

CODECS = {37: 'cp037', 500: 'cp500'}


def read_record(raw, ccsid):
    if type(ccsid) is not int or ccsid not in CODECS:
        raise ValueError('An explicit supported CCSID (37 or 500) is required')
    if len(raw) != 13:
        raise ValueError('The synthetic record must contain exactly 13 bytes')
    label = raw[:8].decode(CODECS[ccsid], errors='strict')
    if not all(character.isprintable() for character in label):
        raise ValueError('Control characters are forbidden in the label field')
    return {'label': label, 'packedHex': raw[8:11].hex(),
            'counter': int.from_bytes(raw[11:13], byteorder='big', signed=False)}
