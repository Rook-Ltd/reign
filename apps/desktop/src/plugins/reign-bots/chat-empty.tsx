/**
 * What a bot's chat shows before it has said anything.
 *
 * The quiet Rook imagemark core's splash uses, with the bot's name under it,
 * so an empty conversation still says whose it is.
 */

import { host, useValue } from '@reign/plugin-sdk'

import { $botMeta, $lastRoster } from './data'
import { useBots } from './i18n'
import { displayName } from './labels'
import { botRosterMeta } from './routing'
import type { RosterRow } from './types'

// The Rook imagemark, masked so it renders in the theme's foreground.
const ROOK_MARK_MASK = `url(${import.meta.env.BASE_URL}rook-mark-outline.svg) center / contain no-repeat`
const ROOK_MARK_STYLE = { mask: ROOK_MARK_MASK, WebkitMask: ROOK_MARK_MASK }

/** The bot whose canonical chat this session is, if it is one. Matches the
 *  durable registry id or the compression-lineage tip, the same pair the
 *  roster's click and preview identity resolve through. */
function botForStoredId(roster: readonly RosterRow[], storedId: string): null | RosterRow {
  if (!storedId || !Array.isArray(roster)) {
    return null
  }

  return (
    roster.find(bot => {
      const canonical = bot?.canonical_session

      return String(canonical?.id ?? '') === storedId || String(canonical?.resolved_id ?? '') === storedId
    }) ?? null
  )
}

/** The stored id of the chat on screen. The transcript hands its slot the
 *  RUNTIME id, and a canonical Bot Chat is keyed by its stored one — the same
 *  two id spaces that misrouted Bot Mode's RPCs in #93080. The focus store is
 *  the translation the rest of the plugin already trusts. */
function focusedStoredId(): string {
  return String(host.state.focusedStoredSessionId?.get?.() ?? '')
}

function botForChat(roster: readonly RosterRow[], sessionId: string): null | RosterRow {
  // Stored ids pass straight through, so a shell that hands us one still
  // resolves; otherwise the focused chat is the empty one being looked at.
  return botForStoredId(roster, sessionId) ?? botForStoredId(roster, focusedStoredId())
}

export function BotChatEmpty({ sessionId }: { sessionId: string }) {
  const b = useBots()
  // Subscribed, not read once: roster, metadata and focus all land after the
  // transcript mounts. This is also how the state appears at all — the slot
  // mounts for every empty session and only resolves to a bot once the roster
  // is in hand.
  const roster = useValue($lastRoster)
  const allMeta = useValue($botMeta)
  useValue(host.state.focusedStoredSessionId)
  const bot = botForChat(roster, sessionId)

  if (!bot) {
    return null
  }

  // Route-keyed, exactly as the roster row resolves it: metadata is scoped to
  // the gateway it came from, so a plain by-name read misses the entry a
  // source-scoped bot's avatar actually lives under.
  const meta = botRosterMeta(bot, allMeta)
  const name = displayName(bot, meta)

  return (
    <div
      className="pointer-events-none flex w-full min-w-0 flex-col items-center justify-center px-0.5 py-6 text-center text-muted-foreground sm:px-6 lg:px-8"
      data-slot="bot_chat_empty"
    >
      <div className="w-full min-w-0">
        <span
          aria-hidden="true"
          className="mx-auto mb-6 block size-28 bg-foreground/20 sm:size-36"
          style={ROOK_MARK_STYLE}
        />

        <h2 className="m-0 mb-1 truncate text-lg font-medium tracking-tight text-foreground/80">{name}</h2>

        <p className="m-0 text-center leading-normal tracking-tight">{b.bot.chatEmpty}</p>
      </div>
    </div>
  )
}
