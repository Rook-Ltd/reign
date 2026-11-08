// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const desktopWindow = window as unknown as { reignDesktop?: Partial<Window['reignDesktop']> }

// The bridge reports native capability as a fact, so no host OS is faked.
async function loadTranslucency(host: 'browser' | 'electron') {
  document.documentElement.dataset.reignDesktopHost = host
  desktopWindow.reignDesktop = { glassSupported: true, translucencySupported: true }
  vi.resetModules()

  return import('@/store/translucency')
}

describe('browser translucency capability', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-reign-desktop-host')
  })

  afterEach(() => {
    Reflect.deleteProperty(desktopWindow, 'reignDesktop')
    vi.restoreAllMocks()
    vi.resetModules()
  })

  it('disables native window translucency in the browser host even when the bridge reports support', async () => {
    const translucency = await loadTranslucency('browser')

    expect(translucency.GLASS_SUPPORTED).toBe(false)
    expect(translucency.TRANSLUCENCY_SUPPORTED).toBe(false)
  })

  it('retains native capability detection outside the browser host', async () => {
    const translucency = await loadTranslucency('electron')

    expect(translucency.TRANSLUCENCY_SUPPORTED).toBe(true)
  })
})
