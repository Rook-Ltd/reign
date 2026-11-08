# shellcheck shell=sh
# Installed as /etc/profile.d/reign.sh. Debian's /etc/profile resets PATH for
# every login shell (`bash -l`, `docker exec <c> bash -l`, ssh, the terminal
# tool's background `bash -lic`), dropping the image's ENV PATH dirs, so bare
# `reign` exits 127 there. Put them back in the ENV PATH order; dirs a login
# PATH already lists keep their position.
for __reign_p in /opt/data/.local/bin /opt/reign/.venv/bin /opt/reign/bin; do
    case ":$PATH:" in
        *":$__reign_p:"*) ;;
        *) PATH="$__reign_p:$PATH" ;;
    esac
done
unset __reign_p
export PATH
