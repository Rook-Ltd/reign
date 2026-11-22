import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'

import { expect, test } from 'vitest'

import { runGatewayEnsure, runGatewayOwnerRestart } from './local-gateway'

// A real bounded client against a fake `reign`: `new` knows `--detach`; `old` predates it and
// rejects it the way argparse does. Each run appends its argv, so the test reads what was executed.
async function fakeReign(kind: 'new' | 'old') {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'gw-detach-'))
  const calls = path.join(dir, 'calls')

  const reject =
    kind === 'old'
      ? 'case " $* " in *" --detach "*) echo "reign: error: unrecognized arguments: --detach" >&2; exit 2;; esac\n'
      : ''

  const bin = path.join(dir, 'reign')
  await fs.writeFile(bin, `#!/bin/sh\necho "$*" >> "${calls}"\n${reject}echo "✓ restarted"\n`, { mode: 0o755 })
  const run = (args: string[]) =>
    runGatewayEnsure(
      { command: bin, args, env: {}, shell: false },
      dir,
      dir,
      {},
      { timeoutMs: 5000, label: 'reign gateway restart' }
    )

  return { run, calls: async () => (await fs.readFile(calls, 'utf8')).trim().split('\n') }
}

test.skipIf(process.platform === 'win32')('a stale-owner restart asks for a detached replacement', async () => {
  const reign = await fakeReign('new')
  const result = await runGatewayOwnerRestart(reign.run, 'work')

  expect(result.code).toBe(0)
  expect(await reign.calls()).toEqual(['--profile work gateway restart --detach'])
})

// apps/desktop/AGENTS.md "Compatibility": a runtime older than `--detach` still restarts (its old
// behaviour, which works under a service) instead of failing on the flag and leaving the stale owner.
test.skipIf(process.platform === 'win32')('a runtime that predates --detach still restarts the owner', async () => {
  const reign = await fakeReign('old')
  const result = await runGatewayOwnerRestart(reign.run, 'default')

  expect(result.code).toBe(0)
  expect(await reign.calls()).toEqual([
    '--profile default gateway restart --detach',
    '--profile default gateway restart'
  ])
})
