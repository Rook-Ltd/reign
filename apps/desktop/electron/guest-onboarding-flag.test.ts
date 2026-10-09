import assert from 'node:assert/strict'

import { test } from 'vitest'

import { desktopBackendSpawnEnv, guestOnboardingEnabled, skipIntroEnabled } from './guest-onboarding'
import { buildSpawnCommand } from './remote-lifecycle'

test('skipIntroEnabled: exactly "1" in env or --skip-intro on argv skips the first-run film', () => {
  assert.equal(skipIntroEnabled([], { REIGN_SKIP_INTRO: '1' }), true)
  assert.equal(skipIntroEnabled(['electron', '.', '--skip-intro'], {}), true)

  assert.equal(skipIntroEnabled([], {}), false)
  assert.equal(skipIntroEnabled([], { REIGN_SKIP_INTRO: 'true' }), false)
})

test('guestOnboardingEnabled: exactly "1" in env or --guest-onboarding on argv turns the free tier on', () => {
  assert.equal(guestOnboardingEnabled([], { REIGN_GUEST_ONBOARDING: '1' }), true)
  assert.equal(guestOnboardingEnabled(['electron', '.', '--guest-onboarding'], {}), true)

  assert.equal(guestOnboardingEnabled([], {}), false)
  assert.equal(guestOnboardingEnabled([], { REIGN_GUEST_ONBOARDING: 'true' }), false)
  assert.equal(guestOnboardingEnabled([], { REIGN_GUEST_ONBOARDING: '0' }), false)
  assert.equal(guestOnboardingEnabled(['electron', '.', '--local'], { REIGN_GUEST_ONBOARDING: '' }), false)
})

test('desktopBackendSpawnEnv stamps the launch decision last and never lets an inherited value leak', () => {
  const base = {
    REIGN_HOME: '/tmp/home',
    REIGN_DESKTOP: '1',
    REIGN_GUEST_ONBOARDING: '1',
    PATH: '/usr/bin'
  }

  const on = desktopBackendSpawnEnv({ ...base, REIGN_GUEST_ONBOARDING: '0' }, true)
  assert.equal(on.REIGN_GUEST_ONBOARDING, '1')

  const off = desktopBackendSpawnEnv(base, false)
  assert.equal(off.REIGN_GUEST_ONBOARDING, '0', 'a stray inherited "1" must not turn the free tier on')

  for (const env of [on, off]) {
    assert.equal(env.REIGN_HOME, base.REIGN_HOME)
    assert.equal(env.REIGN_DESKTOP, base.REIGN_DESKTOP)
    assert.equal(env.PATH, base.PATH)
  }
})

test('remote SSH spawn command carries REIGN_GUEST_ONBOARDING=1 only when the launch decided on', () => {
  const on = buildSpawnCommand('/x/reign', 'work', { logPath: '~/.reign/log', guestOnboarding: true })
  assert.match(on, /exec env REIGN_DESKTOP=1 REIGN_GUEST_ONBOARDING=1 /)

  const off = buildSpawnCommand('/x/reign', 'work', { logPath: '~/.reign/log', guestOnboarding: false })
  assert.match(off, /exec env REIGN_DESKTOP=1 /)
  assert.doesNotMatch(off, /REIGN_GUEST_ONBOARDING/)

  const unset = buildSpawnCommand('/x/reign', 'work', { logPath: '~/.reign/log' })
  assert.doesNotMatch(unset, /REIGN_GUEST_ONBOARDING/)
})
