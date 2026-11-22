"""Shell-path patterns for the Reign home and its protected stores (#109367).

The terminal approval gate (tools.approval_detection) prompts before destructive verbs reach these
targets; the store list is REIGN_PROTECTED_SUBPATHS, shared with agent.file_safety's write deny.
"""
import re

from reign_cli.home_data_layout import REIGN_PROTECTED_SUBPATHS

# The Reign home itself and the application-owned stores the file tools refuse to write
# (REIGN_PROTECTED_SUBPATHS: state.db, sessions/, vault/, ...). Destroying them is recoverable only
# from backup, so destructive shell verbs on these targets prompt; reads and copies OUT stay clean.
_REIGN_HOME_ROOT = r'(?:~/\.reign|(?:\$home|\$\{home\})/\.reign|(?:\$reign_home|\$\{reign_home\}))'
_PATH_WORD_END = r'["\']?(?=[\s"\'`;|&<>()]|$)'
# A store, its SQLite sidecars (state.db-wal) or a path inside a directory store (sessions/x.jsonl).
# Neighbours such as state.db.bak or sessions-old.tar are not stores (agent.file_safety agrees).
_REIGN_STORE_FILE = (
    _REIGN_HOME_ROOT + r'/(?:' + '|'.join(
        re.escape(sub) + (r'(?:-wal|-shm|-journal)?' if sub.endswith('.db') else r'(?:/[^\s"\'`;|&<>()]*)?')
        for sub in REIGN_PROTECTED_SUBPATHS) + r')' + _PATH_WORD_END
)
# Overwrites inside credential directories must prompt (vault.key, MCP OAuth tokens, browser cookies).
# New session transcript files stay clean, as before; only the sessions/ root is an overwrite target.
_REIGN_STORE_ROOT = (
    _REIGN_HOME_ROOT + r'/(?:' + '|'.join(
        re.escape(sub) + (
            r'(?:-wal|-shm|-journal)?' if sub.endswith('.db')
            else r'/?' if sub == 'sessions' else r'(?:/[^\s"\'`;|&<>()]*)?'
        )
        for sub in REIGN_PROTECTED_SUBPATHS) + r')' + _PATH_WORD_END
)
_REIGN_HOME_BARE = rf'{_REIGN_HOME_ROOT}/?\*?{_PATH_WORD_END}'
_REIGN_STORE_PATH = rf'(?:{_REIGN_STORE_FILE}|{_REIGN_HOME_BARE})'
