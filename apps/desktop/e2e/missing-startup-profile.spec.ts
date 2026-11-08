import fs from 'node:fs'
import path from 'node:path'

import { waitForChatReady } from '../../../tests-js/scripts/desktop-chat-smoke'
import { writeEnvFile, writeMockProviderConfig } from '../../../tests-js/scripts/mock-provider-config'
import { startMockServer } from '../../../tests-js/scripts/mock-server'

import { buildAppEnv, createSandbox, launchDesktop } from './fixtures'
import { expect, test } from './test'

// Electron userData outlives a Reign reinstall that wipes REIGN_HOME, so the
// remembered startup profile (and an explicit default) can name a profile this
// home no longer has. Every boot then ran `reign --profile <gone> gateway
// ensure`, which refuses a missing profile, and Desktop never started.
test('a remembered profile missing from a reinstalled Reign home boots the default profile', async () => {
  test.setTimeout(300_000)
  const sandbox = createSandbox('missing-startup-profile')
  const mock = await startMockServer()
  writeMockProviderConfig(sandbox.reignHome, mock.url)
  writeEnvFile(sandbox.reignHome)

  const preferences = path.join(sandbox.userDataDir, 'active-profile.json')
  const gone = { connectionId: null, profile: 'reign-contributor' }
  fs.writeFileSync(preferences, JSON.stringify({ profile: gone.profile, defaultRoute: gone }))

  let app: Awaited<ReturnType<typeof launchDesktop>>['app'] | undefined

  try {
    const launched = await launchDesktop(buildAppEnv(sandbox))
    app = launched.app

    await waitForChatReady(launched.page, 180_000)

    // The composer can paint before a failed boot raises its overlay; a REST
    // round trip through main proves the gateway actually came up.
    const status = await launched.page.evaluate(() => (window as any).reignDesktop.api({ path: '/api/status' }))
    expect(status).toBeTruthy()
    expect(JSON.parse(fs.readFileSync(preferences, 'utf8'))).toMatchObject({ profile: 'default', defaultRoute: null })
    expect(await launched.page.evaluate(() => (window as any).reignDesktop.profile.get())).toEqual({
      profile: 'default'
    })
  } finally {
    await app?.close().catch(() => undefined)
    await mock.close()
    sandbox.cleanup()
  }
})
