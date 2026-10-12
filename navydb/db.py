import pathlib, sqlite3
ROOT = pathlib.Path(__file__).resolve().parent.parent

def connect(path=ROOT / "data" / "navy.db"):
    con = sqlite3.connect(path)
    con.executescript((ROOT / "navydb" / "schema.sql").read_text())
    return con
