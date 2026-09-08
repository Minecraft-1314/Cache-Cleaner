"""Full user-editable cache suffix catalog."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SuffixRule:
    token: str
    kind: str = "ext"
    risky: bool = False
    group: str = "general"


SUFFIX_GROUPS = ("general", "browser", "build", "index", "vcs")

SUFFIX_RULES = (
    SuffixRule(".cache"),
    SuffixRule(".tmp"),
    SuffixRule(".temp"),
    SuffixRule(".part"),
    SuffixRule(".crdownload"),
    SuffixRule(".partial"),
    SuffixRule(".download"),
    SuffixRule(".opdownload"),
    SuffixRule(".bak", risky=True),
    SuffixRule(".old", risky=True),
    SuffixRule(".log", risky=True),
    SuffixRule(".swp"),
    SuffixRule(".swo"),
    SuffixRule(".db", risky=True),
    SuffixRule(".blob"),
    SuffixRule(".dmp", risky=True),
    SuffixRule(".etl", risky=True),
    SuffixRule(".hprof", risky=True),
    SuffixRule(".thumb"),
    SuffixRule(".thumbdata"),
    SuffixRule("Thumbs.db", kind="name"),
    SuffixRule(".ost", risky=True),
    SuffixRule(".edb", risky=True),
    SuffixRule(".cab", risky=True),
    SuffixRule(".msu", risky=True),
    SuffixRule(".cfa"),
    SuffixRule(".pek"),
    SuffixRule(".asd"),
    SuffixRule(".ldb", group="browser"),
    SuffixRule(".f", group="browser", risky=True),
    SuffixRule(".pyc", group="build"),
    SuffixRule(".pyo", group="build"),
    SuffixRule(".class", group="build"),
    SuffixRule(".o", group="build"),
    SuffixRule(".obj", group="build"),
    SuffixRule(".gch", group="build"),
    SuffixRule(".pch", group="build"),
    SuffixRule(".ipch", group="build"),
    SuffixRule(".ncb", group="build"),
    SuffixRule(".pdb", group="build", risky=True),
    SuffixRule(".rmeta", group="build"),
    SuffixRule(".rlib", group="build"),
    SuffixRule(".aux", group="build"),
    SuffixRule(".toc", group="build"),
    SuffixRule(".lof", group="build"),
    SuffixRule(".lot", group="build"),
    SuffixRule(".bbl", group="build"),
    SuffixRule(".blg", group="build"),
    SuffixRule(".lastupdated", group="build"),
    SuffixRule(".nupkg", group="build", risky=True),
    SuffixRule(".tsbuildinfo", group="build"),
    SuffixRule("-journal", kind="ends", group="index", risky=True),
    SuffixRule("-wal", kind="ends", group="index", risky=True),
    SuffixRule("-shm", kind="ends", group="index", risky=True),
    SuffixRule(".cfs", group="index"),
    SuffixRule(".cfe", group="index"),
    SuffixRule(".si", group="index"),
    SuffixRule(".fdt", group="index"),
    SuffixRule(".fdx", group="index"),
    SuffixRule(".fnm", group="index"),
    SuffixRule(".tim", group="index"),
    SuffixRule(".tip", group="index"),
    SuffixRule(".doc", group="index", risky=True),
    SuffixRule(".pos", group="index", risky=True),
    SuffixRule(".pay", group="index", risky=True),
    SuffixRule(".nvd", group="index"),
    SuffixRule(".nvm", group="index"),
    SuffixRule(".dvd", group="index"),
    SuffixRule(".dii", group="index"),
    SuffixRule(".tvx", group="index"),
    SuffixRule(".tvd", group="index"),
    SuffixRule(".tvf", group="index"),
    SuffixRule(".idx", group="vcs", risky=True),
    SuffixRule(".pack", group="vcs", risky=True),
    SuffixRule(".deb", group="vcs", risky=True),
    SuffixRule(".rpm", group="vcs", risky=True),
    SuffixRule("pkg.tar.zst", kind="ends", group="vcs", risky=True),
)


def get_suffix_rules():
    return SUFFIX_RULES


def get_default_suffix_tokens():
    return [rule.token for rule in SUFFIX_RULES if not rule.risky]
