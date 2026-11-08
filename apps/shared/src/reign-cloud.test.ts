import { describe, expect, it } from 'vitest'

import { isReignCloudUrl } from './reign-cloud'

describe('isReignCloudUrl', () => {
  it('recognises production and staging agent hosts, nothing else', () => {
    expect(isReignCloudUrl('https://ares-3009.agents.nousresearch.com')).toBe(true)
    expect(isReignCloudUrl('https://ares--app.agents.staging-nousresearch.com/')).toBe(true)
    expect(isReignCloudUrl('https://agents.nousresearch.com.evil.example')).toBe(false)
    expect(isReignCloudUrl('https://my-box.tailnet.ts.net')).toBe(false)
    expect(isReignCloudUrl('not a url')).toBe(false)
    expect(isReignCloudUrl(undefined)).toBe(false)
  })
})
