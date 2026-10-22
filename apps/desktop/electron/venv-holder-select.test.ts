import assert from 'node:assert/strict'

import { test } from 'vitest'

import { hasWindowsPathPrefix, isExternalVenvHolder, isReignOwnedVenvDaemon } from './venv-holder-select'

const SCRIPTS = 'C:\\Reign\\venv\\Scripts'

test('matches the hindsight daemon shim (exe under venv Scripts + hindsight cmdline)', () => {
  assert.equal(
    isReignOwnedVenvDaemon(
      'C:\\Reign\\venv\\Scripts\\pythonw.exe',
      'C:\\Reign\\venv\\Scripts\\pythonw.exe -m hindsight_api.main --daemon --idle-timeout 300 --port 9177',
      SCRIPTS
    ),
    true
  )
})

test('Windows path prefix match is ordinal case-insensitive', () => {
  assert.equal(
    isReignOwnedVenvDaemon(
      'c:\\reign\\venv\\scripts\\python.exe',
      'python.exe -m hindsight_api.main --daemon',
      'C:\\Reign\\venv\\Scripts'
    ),
    true
  )
})

test('excludes external venv holders that are not the hindsight daemon', () => {
  // a user terminal running the reign CLI from the venv — must NOT be killed
  assert.equal(isReignOwnedVenvDaemon('C:\\Reign\\venv\\Scripts\\reign.exe', 'reign chat -q "hi"', SCRIPTS), false)
  // an unrelated python script using the venv interpreter
  assert.equal(
    isReignOwnedVenvDaemon('C:\\Reign\\venv\\Scripts\\python.exe', 'python C:\\tools\\import.py', SCRIPTS),
    false
  )
})

test('excludes exes outside the venv even when the cmdline mentions hindsight', () => {
  assert.equal(
    isReignOwnedVenvDaemon('C:\\Other\\pythonw.exe', 'pythonw -m hindsight_api.main --daemon', SCRIPTS),
    false
  )
})

test('prefix boundary: sibling dirs (ScriptsX) do not match', () => {
  assert.equal(hasWindowsPathPrefix('C:\\Reign\\venv\\ScriptsX\\python.exe', SCRIPTS), false)
  assert.equal(hasWindowsPathPrefix('C:\\Reign\\venv\\Scripts\\python.exe', SCRIPTS), true)
})

test('null/undefined fields never match', () => {
  assert.equal(isReignOwnedVenvDaemon(null, 'x', SCRIPTS), false)
  assert.equal(isReignOwnedVenvDaemon('C:\\Reign\\venv\\Scripts\\pythonw.exe', null, SCRIPTS), false)
  assert.equal(isReignOwnedVenvDaemon(undefined, undefined, SCRIPTS), false)
})

// --- isExternalVenvHolder (#62311) ------------------------------------------

test('matches the autostart gateway shim (reign.exe under venv Scripts)', () => {
  assert.equal(
    isExternalVenvHolder(
      'C:\\Reign\\venv\\Scripts\\reign.exe',
      '"C:\\Reign\\venv\\Scripts\\reign.exe" gateway run --external-supervisor',
      SCRIPTS
    ),
    true
  )
})

test('matches the dashboard scheduled task (python -m reign_cli / -m reign)', () => {
  assert.equal(
    isExternalVenvHolder(
      'C:\\Reign\\venv\\Scripts\\python.exe',
      '"C:\\Reign\\venv\\Scripts\\python.exe" -m reign_cli.main dashboard',
      SCRIPTS
    ),
    true
  )
  assert.equal(
    isExternalVenvHolder('C:\\Reign\\venv\\Scripts\\pythonw.exe', 'pythonw.exe -m reign serve', SCRIPTS),
    true
  )
})

test('never matches an unrelated process that merely borrows the venv interpreter', () => {
  // a user's own script running on the venv python — NOT Reign, must NOT be killed
  assert.equal(
    isExternalVenvHolder('C:\\Reign\\venv\\Scripts\\python.exe', 'python C:\\tools\\import.py', SCRIPTS),
    false
  )
  // hindsight daemon is selected by isReignOwnedVenvDaemon, not here
  assert.equal(
    isExternalVenvHolder('C:\\Reign\\venv\\Scripts\\pythonw.exe', 'pythonw -m hindsight_api.main --daemon', SCRIPTS),
    false
  )
})

test('never matches a process outside the venv, even with reign in the cmdline', () => {
  // an editor / shell whose command line mentions the install root (#62445 regression guard)
  assert.equal(
    isExternalVenvHolder('C:\\Windows\\System32\\cmd.exe', 'cmd /c cd C:\\Reign\\venv\\Scripts && dir', SCRIPTS),
    false
  )
  assert.equal(isExternalVenvHolder('C:\\Other\\reign.exe', 'reign gateway run', SCRIPTS), false)
})

test('sibling-dir and boundary safety for the external selector', () => {
  assert.equal(isExternalVenvHolder('C:\\Reign\\venv\\ScriptsX\\reign.exe', 'reign gateway run', SCRIPTS), false)
  assert.equal(isExternalVenvHolder(null, 'reign gateway run', SCRIPTS), false)
  assert.equal(isExternalVenvHolder('C:\\Reign\\venv\\Scripts\\reign.exe', null, SCRIPTS), false)
})
