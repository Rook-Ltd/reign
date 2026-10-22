import assert from 'node:assert/strict'
import os from 'node:os'
import path from 'node:path'

import { afterEach, test, vi } from 'vitest'

import { platformDefaultReignHome, resolveDesktopReignHome, resolveDesktopUserData } from './data-paths'
import { controlSocketPath } from './ssh-connection'

afterEach((): void => {
  vi.unstubAllEnvs()
})

test.skipIf(process.platform === 'win32')('local SSH sockets use the suffixed default root', (): void => {
  vi.stubEnv('REIGN_DATA_DIR_SUFFIX', 'magic-test')
  const socket: string = controlSocketPath('user', 'host', 22)

  assert.equal(path.dirname(socket), path.join(platformDefaultReignHome(os.homedir()), 'desktop-ssh'))
})

test('default data roots append the suffix literally on each platform', (): void => {
  for (const platform of ['linux', 'darwin', 'win32'] as const) {
    const paths: typeof path = platform === 'win32' ? path.win32 : path.posix
    const home: string = platform === 'win32' ? 'C:\\Users\\test' : '/home/test'
    const local: string = paths.join(home, 'AppData', 'Local')
    const userData: string = paths.join(home, 'app-data', 'Reign')
    const base: string = platform === 'win32' ? paths.join(local, 'reign') : paths.join(home, '.reign')

    for (const suffix of ['', '-asdfasdf', 'magic-test', ' spaced ']) {
      const env: NodeJS.ProcessEnv = { LOCALAPPDATA: local, REIGN_DATA_DIR_SUFFIX: suffix }

      assert.equal(platformDefaultReignHome(home, env, platform), base + suffix)
      assert.equal(resolveDesktopUserData(userData, env), userData + suffix)
      assert.equal(
        resolveDesktopReignHome({ home, env, platform, directoryExists: (): boolean => false }),
        base + suffix
      )
    }
  }
})

test('explicit homes and userData retain precedence, and suffixed Windows homes never use legacy state', (): void => {
  const home: string = '/home/test'

  const env: NodeJS.ProcessEnv = {
    REIGN_DATA_DIR_SUFFIX: 'magic-test',
    REIGN_HOME: '/explicit/home',
    REIGN_DESKTOP_USER_DATA_DIR: '/explicit/electron'
  }

  assert.equal(resolveDesktopUserData('/default/electron', env), path.resolve(env.REIGN_DESKTOP_USER_DATA_DIR!))
  assert.equal(resolveDesktopReignHome({ home, env, platform: 'linux' }), env.REIGN_HOME)
  delete env.REIGN_HOME
  assert.equal(resolveDesktopReignHome({ home, env, platform: 'linux' }), '/explicit/electron/reign-home')

  const windowsHome: string = 'C:\\Users\\test'
  const windowsEnv: NodeJS.ProcessEnv = { REIGN_DATA_DIR_SUFFIX: 'magic-test' }
  const expected: string = path.win32.join(windowsHome, 'AppData', 'Local', 'reignmagic-test')

  assert.equal(
    resolveDesktopReignHome({
      home: windowsHome,
      env: windowsEnv,
      platform: 'win32',
      directoryExists: (): boolean => true
    }),
    expected
  )
  assert.equal(
    resolveDesktopReignHome({
      home: windowsHome,
      env: windowsEnv,
      platform: 'win32',
      readWindowsHome: (): string => 'C:\\custom'
    }),
    'C:\\custom'
  )
})
