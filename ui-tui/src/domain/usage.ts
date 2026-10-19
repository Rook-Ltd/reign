import type { Usage } from '@reign/shared/gateway-events'

export { usageFromTick } from '@reign/shared/usage-tick'

export const ZERO: Usage = { calls: 0, input: 0, output: 0, total: 0 }
