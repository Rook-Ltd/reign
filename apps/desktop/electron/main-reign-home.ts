// The Reign home the desktop main process runs against, resolved once at boot.
// Resolving it here also registers it with the file-preview read guard, so the
// home's (and every profile's) credential stores are refused before any IPC
// read can be served.

import { resolveDesktopReignHome } from './data-paths'
import { directoryExists } from './fs-probes'
import { setSensitiveReignHome } from './hardening'
import { readWindowsUserEnvVar } from './windows-user-env'

export function resolveMainReignHome(home: string): string {
  const reignHome = resolveDesktopReignHome({
    home,
    directoryExists,
    readWindowsHome: (): string | null => readWindowsUserEnvVar('REIGN_HOME')
  })

  setSensitiveReignHome(reignHome)

  return reignHome
}
