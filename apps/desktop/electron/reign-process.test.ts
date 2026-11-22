import { describe, expect, it } from 'vitest'

import { commandLineIsReignRuntime } from './reign-process'

// HX003: process identity comes from a whole argv TOKEN, never an argv substring.
describe('commandLineIsReignRuntime (HX003 token matching)', () => {
  it('matches a real Reign gateway command line', () => {
    expect(commandLineIsReignRuntime('reign\0gateway\0run')).toBe(true)
    expect(commandLineIsReignRuntime('reign gateway run')).toBe(true)
    expect(commandLineIsReignRuntime('reign --profile work gateway run')).toBe(true)
  })

  it('matches a Reign launched by an interpreter (basename of a path token)', () => {
    expect(commandLineIsReignRuntime('/venv/bin/python\0/venv/bin/reign\0gateway\0run')).toBe(true)
    expect(commandLineIsReignRuntime('C:\\Reign\\reign.exe gateway run')).toBe(true)
  })

  // The bug this replaces: a bare `.includes('reign')` matched any of these.
  it('does NOT match an unrelated process whose path merely contains "reign"', () => {
    expect(commandLineIsReignRuntime('vim /home/user/reign-notes.txt')).toBe(false)
    expect(commandLineIsReignRuntime('/opt/reignbrew/bin/tool --run')).toBe(false)
    expect(commandLineIsReignRuntime('node /srv/reign-dashboard/server.js')).toBe(false)
    expect(commandLineIsReignRuntime('cat ~/.reign/config.yaml')).toBe(false)
  })

  // G2 (#150283): the real unmanaged-gateway launch is `python -m reign_cli.main … gateway
  // run`, which the executable-basename-only matcher REJECTED — so findRunningGatewayProfiles
  // missed a live gateway at first launch / profile repair. Mirror the canonical Python matcher
  // (gateway.status.looks_like_gateway_command_line): recognize the module entry point, by argv
  // TOKENS not a substring, carrying the gateway subcommand.
  it('matches a module-launched gateway (python -m reign_cli.main … gateway run)', () => {
    expect(commandLineIsReignRuntime('python\0-m\0reign_cli.main\0-p\0x\0gateway\0run')).toBe(true)
    expect(commandLineIsReignRuntime('python -m reign_cli.main -p x gateway run')).toBe(true)
    expect(commandLineIsReignRuntime('/venv/bin/python /venv/lib/reign_cli/main.py gateway run')).toBe(true)
    expect(commandLineIsReignRuntime('python -m reign_cli.main --profile work gateway run')).toBe(true)
  })

  it('does NOT match a module entry without the gateway subcommand, nor an unrelated reign-tool path', () => {
    // A reign_cli.main invocation that is not a gateway (e.g. `chat`) is not a running gateway.
    expect(commandLineIsReignRuntime('python -m reign_cli.main chat')).toBe(false)
    // HX003: no substring; an unrelated tool whose path contains "reign" is never a runtime.
    expect(commandLineIsReignRuntime('/opt/reign-tool/foo gateway run')).toBe(false)
    // `-p gateway` is a profile value, not a subcommand.
    expect(commandLineIsReignRuntime('python -m reign_cli.main -p gateway chat')).toBe(false)
  })
})
