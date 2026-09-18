import { describe, expect, it } from 'vitest'

import {
  normalizeReignOpenString,
  pathFromReignDeepLink,
  pathFromOpenDeepLink,
  resolveReignOpenPath
} from './reign-open-target'

describe('normalizeReignOpenString', () => {
  it('accepts hash-router paths and strips a leading hash', () => {
    expect(normalizeReignOpenString('/index-network/intent/1')).toBe('/index-network/intent/1')
    expect(normalizeReignOpenString('#/index-network/intent/1')).toBe('/index-network/intent/1')
  })

  it('maps plugin-scoped reign:// deep links to the same path', () => {
    expect(normalizeReignOpenString('reign://index-network/intent/1')).toBe('/index-network/intent/1')
    expect(normalizeReignOpenString('reign://index-network/intent/1?focus=true')).toBe(
      '/index-network/intent/1?focus=true'
    )
  })

  it('maps reign://open/… deep links by stripping the open host', () => {
    expect(normalizeReignOpenString('reign://open/index-network/intent/1')).toBe('/index-network/intent/1')
    expect(normalizeReignOpenString('reign://open/settings/plugins')).toBe('/settings/plugins')
  })

  it('rejects reserved reign kinds and unsafe paths', () => {
    expect(normalizeReignOpenString('reign://blueprint/morning-brief')).toBeNull()
    expect(normalizeReignOpenString('reign://plugin/install')).toBeNull()
    expect(normalizeReignOpenString('https://example.com/x')).toBeNull()
    expect(normalizeReignOpenString('/../etc/passwd')).toBeNull()
    expect(normalizeReignOpenString('index-network')).toBeNull()
  })
})

describe('resolveReignOpenPath', () => {
  it('merges structured path + params', () => {
    expect(resolveReignOpenPath({ path: '/index-network/intent/1', params: { focus: 'true' } })).toBe(
      '/index-network/intent/1?focus=true'
    )
  })

  it('resolves href the same as a bare string', () => {
    expect(resolveReignOpenPath({ href: 'reign://index-network/intent/1' })).toBe('/index-network/intent/1')
  })
})

describe('pathFromReignDeepLink', () => {
  it('builds the navigate path from a plugin-scoped deep-link payload', () => {
    expect(pathFromReignDeepLink('index-network', 'intent/1')).toBe('/index-network/intent/1')
  })

  it('builds the navigate path from reign://open/… payloads', () => {
    expect(pathFromOpenDeepLink('index-network/intent/1')).toBe('/index-network/intent/1')
    expect(pathFromReignDeepLink('open', 'agent/42')).toBe('/agent/42')
  })

  it('ignores reserved kinds', () => {
    expect(pathFromReignDeepLink('blueprint', 'morning-brief')).toBeNull()
    expect(pathFromReignDeepLink('plugin', 'install')).toBeNull()
  })
})
