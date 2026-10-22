import { vi } from 'vitest'

import type { ReignApiRequest } from '@/global'

/** Install a fake `window.reignDesktop.api`, the preload bridge every REST helper sends through. */
export function installRestBridge(answer: (request: ReignApiRequest) => object) {
  const api = vi.fn(async (request: ReignApiRequest) => answer(request))

  Object.defineProperty(window, 'reignDesktop', { configurable: true, value: { api } })

  return api
}
