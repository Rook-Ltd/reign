/**
 * @reign belongs to the default bot only while its source has no real
 * (pre-reservation) `reign` profile. With one, the roster shows exactly one
 * @reign — the real profile — and the default answers to @default, so a
 * typed @reign reaches the same profile the backend's message_agent does.
 */

import { describe, expect, it, vi } from 'vitest'

import { botHandle, botMentionTag, claimDefaultHandles, mergeMultiSourceRoster, resolveRosterMentions } from './data'
import { previewKind } from './row-helpers'
import type { RosterRow } from './types'

vi.mock('@reign/plugin-sdk', async () => {
  const { atom } = await import('nanostores')

  return { atom, host: {}, queryClient: undefined, useQuery: vi.fn(), useValue: vi.fn() }
})

vi.mock('./shared', () => ({ getPluginCtx: () => null, ID: 'reign-bots' }))

function roster(names: string[]): RosterRow[] {
  const local = { profiles: names.map(name => ({ name })) }

  // What Electron's buildAgentRoster reports for a single local source: bare-name handles.
  const union = {
    agents: names.map(profile => ({
      connectionId: 'local',
      connectionKind: 'local' as const,
      connectionLabel: 'This device',
      handle: profile,
      profile,
      targetProfile: profile
    })),
    primaryConnectionId: 'local'
  }

  return mergeMultiSourceRoster(local, union, 'local').profiles as RosterRow[]
}

describe('the @reign handle', () => {
  it.each([
    [['default', 'researcher'], 'default'],
    [['default', 'reign', 'researcher'], 'reign']
  ])('roster %j shows one @reign and a typed @reign reaches %s', (names, owner) => {
    const rows = roster(names)
    const handles = rows.map(row => botHandle(row.name, row))

    expect(handles.filter(handle => handle === 'reign')).toHaveLength(1)
    expect(rows.map(row => botMentionTag(row)).filter(tag => tag === 'reign')).toHaveLength(1)
    expect(resolveRosterMentions('@reign ping', rows, { name: 'researcher' }).map(row => row.name)).toEqual([owner])
  })

  it('names the default @default once a real reign profile holds the handle', () => {
    const rows = roster(['default', 'reign', 'researcher'])
    const byName = Object.fromEntries(rows.map(row => [row.name, botHandle(row.name, row)]))

    expect(byName).toEqual({ default: 'default', reign: 'reign', researcher: 'researcher' })
    expect(resolveRosterMentions('@default ping', rows, { name: 'researcher' }).map(row => row.name)).toEqual(['default'])
  })

  it('keeps each source separate: a remote reign profile does not rename the local default', () => {
    const rows = claimDefaultHandles<Partial<RosterRow>>([
      { connectionId: 'local', name: 'default' },
      { connectionId: 'mini', name: 'default' },
      { connectionId: 'mini', name: 'reign' }
    ])

    expect(rows.map(row => botHandle(String(row.name), row))).toEqual(['reign', 'default', 'reign'])
  })

  it("never lets a source's stale 'reign' handle on its default answer @reign", () => {
    // An older backend labels its default @reign even beside a real reign profile.
    const rows = claimDefaultHandles<RosterRow>([
      { connectionId: 'mini', handle: 'reign', name: 'default', remoteSource: true },
      { connectionId: 'mini', handle: 'reign', name: 'reign', remoteSource: true },
      { connectionId: 'local', name: 'researcher' }
    ])

    expect(resolveRosterMentions('@reign ping', rows, { name: 'researcher' }).map(row => row.name)).toEqual(['reign'])
  })

  it('names a DM sender in a row preview by its roster handle', () => {
    const rows = claimDefaultHandles<RosterRow>(
      ['default', 'reign', 'researcher'].map(name => ({ connectionId: 'local', name }))
    )

    const sender = (name: string, list: RosterRow[]) =>
      previewKind(`Message from 🤖 ${name} (@x): hi`, list, 'local').fromBot

    expect([sender('default', rows), sender('reign', rows)]).toEqual(['default', 'reign'])
    // No real reign profile: the default is still @reign (#89484).
    expect(sender('default', claimDefaultHandles<RosterRow>([{ connectionId: 'local', name: 'default' }]))).toBe(
      'reign'
    )
  })
})
