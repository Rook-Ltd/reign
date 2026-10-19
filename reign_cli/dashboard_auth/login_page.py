"""Server-rendered /login page (no React, no SPA bundle, no injected token).

Providers come from the registry; an OAuth provider renders an anchor to
``/auth/login?provider=<name>``, a ``supports_password`` provider renders a
credential form wired by :data:`_PASSWORD_FORM_SCRIPT`. Styling mirrors the
``@nous-research/ui`` design system; fonts load from the SPA's ``/fonts/``
mount, which the gate allowlists pre-auth.

The ``class="provider-btn"`` anchor is test-stable: the suite extracts its
href to walk the OAuth flow.
"""
from __future__ import annotations

import html
from urllib.parse import quote, urlencode

from reign_cli.dashboard_auth import list_session_providers

# Single curly braces are ``str.format`` placeholders; CSS curlies are doubled.
_LOGIN_HTML_TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign in — Reign</title>
<style>
  /* Brand fonts shipped by @nous-research/ui — same files the SPA loads. */
  @font-face {{
    font-family: 'Collapse';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url('/fonts/Collapse-Regular.woff2') format('woff2');
  }}
  @font-face {{
    font-family: 'Collapse';
    font-style: normal;
    font-weight: 700;
    font-display: swap;
    src: url('/fonts/Collapse-Bold.woff2') format('woff2');
  }}
  @font-face {{
    font-family: 'Rules Compressed';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url('/fonts/RulesCompressed-Regular.woff2') format('woff2');
  }}
  @font-face {{
    font-family: 'Rules Compressed';
    font-style: normal;
    font-weight: 600;
    font-display: swap;
    src: url('/fonts/RulesCompressed-Medium.woff2') format('woff2');
  }}

  :root {{
    --background-base: #0B0D0C;
    --background: #0B0D0C;
    --midground: #4A9D6B;
    --foreground: #ffffff;
    --hairline: color-mix(in srgb, #4A9D6B 18%, transparent);
    --hairline-strong: color-mix(in srgb, #4A9D6B 35%, transparent);
  }}

  *, *::before, *::after {{ box-sizing: border-box; }}

  html, body {{
    margin: 0;
    padding: 0;
    min-height: 100%;
    background: var(--background-base);
    color: var(--foreground);
    font-family: 'Collapse', system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    font-size: 16px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }}

  /* Subtle dot-grid backdrop — DS idiom (see `.dither` in globals.css). */
  body {{
    background-image:
      radial-gradient(
        ellipse at top,
        color-mix(in srgb, var(--midground) 6%, transparent) 0%,
        transparent 55%
      ),
      repeating-conic-gradient(
        color-mix(in srgb, var(--midground) 4%, transparent) 0% 25%,
        transparent 0% 50%
      );
    background-size: auto, 3px 3px;
    background-attachment: fixed;
  }}

  /* Layout: vertically center on tall screens, top-anchor on short. */
  body {{
    display: grid;
    place-items: center;
    padding: clamp(1.5rem, 6vh, 6rem) 1.25rem;
  }}

  main {{
    width: 100%;
    max-width: 26rem;
    position: relative;
    animation: slide-up 0.6s ease-out both;
  }}

  @keyframes slide-up {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}

  @media (prefers-reduced-motion: reduce) {{
    main {{ animation: none; }}
  }}

  /* Brand wordmark above the card — same uppercase + wide-tracking
     idiom DS Buttons use. */
  .brand {{
    text-align: center;
    margin-bottom: 1.75rem;
    font-family: 'Rules Compressed', 'Collapse', sans-serif;
    font-weight: 600;
    font-size: 1.05rem;
    letter-spacing: 0.32em;
    text-transform: uppercase;
    color: var(--midground);
  }}
  .brand .mark {{
    display: block;
    width: 56px;
    height: 56px;
    margin: 0 auto 0.9rem;
    color: var(--midground);
  }}
  .brand .dot {{
    display: inline-block;
    width: 6px;
    height: 6px;
    background: var(--midground);
    margin: 0 0.55em 0.18em;
    vertical-align: middle;
    border-radius: 1px;
  }}

  .card {{
    position: relative;
    padding: 2.25rem 2rem 2rem;
    background: color-mix(in srgb, #ffffff 2%, var(--background-base));
    border: 1px solid var(--hairline);
    /* Hairline highlight + bevel shadow — matches DS Button SHADOW_DEFAULT
       (`inset -1px -1px 0 #00000080, inset 1px 1px 0 #ffffff80`) at panel scale. */
    box-shadow:
      inset 1px 1px 0 0 color-mix(in srgb, #ffffff 5%, transparent),
      inset -1px -1px 0 0 rgba(0, 0, 0, 0.4),
      0 24px 60px -20px rgba(0, 0, 0, 0.6);
  }}

  h1 {{
    margin: 0 0 0.4rem;
    font-family: 'Rules Compressed', 'Collapse', sans-serif;
    font-weight: 600;
    font-size: 1.85rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--foreground);
  }}

  .subtitle {{
    margin: 0 0 1.75rem;
    color: color-mix(in srgb, var(--foreground) 65%, transparent);
    font-size: 0.95rem;
  }}

  .provider-list {{
    display: grid;
    gap: 0.75rem;
  }}

  /* Provider button — mirrors DS Button (default variant):
     amber surface, dark text, uppercase + wide tracking, inset bevel. */
  .provider-btn {{
    display: block;
    width: 100%;
    box-sizing: border-box;
    padding: 0.95rem 1rem;
    text-align: center;
    background: var(--midground);
    color: var(--background-base);
    font-family: 'Collapse', sans-serif;
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    text-decoration: none;
    border: 0;
    border-radius: 0;  /* DS Button is squared — no rounded corners. */
    cursor: pointer;
    box-shadow:
      inset 1px 1px 0 0 rgba(255, 255, 255, 0.5),
      inset -1px -1px 0 0 rgba(0, 0, 0, 0.5);
    transition: filter 0.12s ease-out;
  }}
  .provider-btn:hover {{
    filter: brightness(1.08);
  }}
  .provider-btn:active {{
    /* DS Button uses `active:invert` on the default surface. */
    filter: invert(1);
  }}
  .provider-btn:focus-visible {{
    outline: 2px solid var(--midground);
    outline-offset: 3px;
  }}

  /* Password provider form — same visual language as the OAuth buttons:
     squared inputs, hairline borders, amber focus ring. */
  .provider-form {{
    display: grid;
    gap: 0.75rem;
    text-align: left;
  }}
  .form-title {{
    font-family: 'Rules Compressed', 'Collapse', sans-serif;
    font-weight: 600;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: color-mix(in srgb, var(--foreground) 70%, transparent);
  }}
  .field {{
    display: grid;
    gap: 0.3rem;
  }}
  .field-label {{
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: color-mix(in srgb, var(--foreground) 55%, transparent);
  }}
  .field-input {{
    width: 100%;
    box-sizing: border-box;
    padding: 0.7rem 0.8rem;
    background: color-mix(in srgb, #000000 25%, var(--background-base));
    color: var(--foreground);
    border: 1px solid var(--hairline-strong);
    border-radius: 0;
    font-family: 'Collapse', sans-serif;
    font-size: 0.95rem;
  }}
  .field-input:focus-visible {{
    outline: none;
    border-color: var(--midground);
    box-shadow: 0 0 0 1px var(--midground);
  }}
  .form-error {{
    color: #ff6b6b;
    font-size: 0.82rem;
    letter-spacing: 0.02em;
  }}
  .provider-form .provider-btn {{
    margin-top: 0.25rem;
  }}

  footer {{
    margin-top: 1.75rem;
    text-align: center;
    color: color-mix(in srgb, var(--foreground) 45%, transparent);
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    line-height: 1.7;
  }}
  footer .sep {{
    display: inline-block;
    width: 1.5rem;
    height: 1px;
    background: var(--hairline-strong);
    vertical-align: middle;
    margin: 0 0.6em 0.2em;
  }}

  /* Selection — DS uses midground bg + background text. */
  ::selection {{
    background: var(--midground);
    color: var(--background-base);
  }}
</style>
</head>
<body>
<main>
  <div class="brand"><svg class="mark" viewBox="318 22 725 725" aria-hidden="true"><path fill="currentColor" d="M318.4,384.26c0.96-206.32,169.14-366.19,370.02-362.03c193.46,4.01,355,160.07,354.63,362.79 C1042.68,593.46,873.2,749.94,675.7,747.1C479.29,744.28,318.86,585.82,318.4,384.26z M503.46,673.07 c-2.12-11.86,0.08-21.84,7.97-31.29c5.63-6.75,11.75-13.25,18.47-18.9c18.95-15.95,33.34-34.33,35.73-60.08 c0.81-8.76,4.19-11.71,12.95-11.6c4.39,0.06,6.92-1.59,8.09-5.7c0.6-2.08,1.4-4.09,2.03-6.16c9.89-32.63,14.84-66.14,18.31-99.96 c4.28-41.66,5.18-83.46,6.41-125.26c0.11-3.64-1.33-5.32-5-6.06c-8.45-1.7-14.21-7.06-15.96-15.35c-1.23-5.8-4.19-8.26-9.47-9.81 c-9.67-2.85-15.38-9.51-16.85-19.62c-0.46-3.13-1.09-6.24-1.44-9.38c-2.97-26.79-5.88-53.58-8.84-80.37 c-0.56-5.01,0.43-6.29,5.59-6.31c10.17-0.05,20.34,0.11,30.5-0.07c4.27-0.08,5.98,1.41,5.88,5.82c-0.23,9.66,0.04,19.33-0.13,29 c-0.07,3.75,0.96,5.62,5.07,5.3c3.65-0.28,7.34-0.24,10.99-0.01c3.81,0.24,4.92-1.44,4.87-5.02c-0.15-9.5-0.06-19-0.05-28.5 c0.01-6.13,0.39-6.53,6.54-6.53c36.83-0.01,73.66-0.01,110.5,0c5.99,0,6.39,0.42,6.41,6.63c0.02,9.5,0.1,19-0.04,28.5 c-0.05,3.6,1.17,5.18,4.95,4.92c3.82-0.26,7.67-0.22,11.49-0.01c3.3,0.18,4.35-1.11,4.3-4.34c-0.16-9.66-0.07-19.33-0.05-29 c0.02-6,0.69-6.68,6.53-6.7c9.5-0.02,19-0.01,28.5,0c6.91,0.01,7.66,0.88,6.86,7.95c-0.95,8.43-1.91,16.86-2.86,25.29 c-2.27,20.17-4.65,40.32-6.75,60.5c-1.26,12.03-7.48,19.71-19.13,22.7c-4.29,1.1-6.23,3.37-7.14,7.68 c-1.79,8.47-6.93,14.57-15.55,16.43c-4.65,1-5.8,2.97-5.71,7.4c1.13,54.15,3.07,108.23,11.24,161.9c3.38,22.2,7.35,44.23,14.39,65.6 c2.67,8.12,2.75,8.09,11.02,8.45c5.83,0.25,9.6,3.49,10.67,9.25c0.4,2.13,0.66,4.28,1.02,6.41c2.94,17.17,9.43,32.46,22.73,44.39 c8.18,7.34,16.2,14.88,23.97,22.65c10.94,10.96,18.53,23.35,14.44,40.11c120.53-71.17,193.5-220.05,155.76-374.55 c-36.31-148.62-170-260.35-332.39-259.93C510,39.89,377.25,161.07,346.2,311.16C315.59,459.1,385.38,603.1,503.46,673.07z"/></svg>Reign</div>
  <div class="card">
    <h1>Sign in</h1>
    <p class="subtitle">Choose a sign-in method to continue to the Reign dashboard.</p>
    <div class="provider-list">
{provider_buttons}
    </div>
  </div>
  <footer>
    <span class="sep"></span>Public bind &middot; Auth required<span class="sep"></span>
  </footer>
</main>
{password_script}
</body>
</html>
"""

_EMPTY_HTML = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign-in unavailable — Reign</title>
<style>
  @font-face {
    font-family: 'Collapse';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url('/fonts/Collapse-Regular.woff2') format('woff2');
  }
  @font-face {
    font-family: 'Rules Compressed';
    font-style: normal;
    font-weight: 600;
    font-display: swap;
    src: url('/fonts/RulesCompressed-Medium.woff2') format('woff2');
  }
  :root {
    --background-base: #0B0D0C;
    --midground: #4A9D6B;
    --foreground: #ffffff;
    --hairline: color-mix(in srgb, #4A9D6B 18%, transparent);
  }
  *, *::before, *::after { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; min-height: 100%;
    background: var(--background-base);
    color: var(--foreground);
    font-family: 'Collapse', system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    font-size: 16px; line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }
  body {
    display: grid; place-items: center;
    padding: clamp(1.5rem, 6vh, 6rem) 1.25rem;
  }
  main {
    width: 100%; max-width: 32rem;
    padding: 2.25rem 2rem;
    background: color-mix(in srgb, #ffffff 2%, var(--background-base));
    border: 1px solid var(--hairline);
    box-shadow:
      inset 1px 1px 0 0 color-mix(in srgb, #ffffff 5%, transparent),
      inset -1px -1px 0 0 rgba(0, 0, 0, 0.4),
      0 24px 60px -20px rgba(0, 0, 0, 0.6);
  }
  h1 {
    margin: 0 0 1rem;
    font-family: 'Rules Compressed', 'Collapse', sans-serif;
    font-weight: 600; font-size: 1.5rem;
    letter-spacing: 0.05em; text-transform: uppercase;
    color: var(--midground);
  }
  p { margin: 0 0 1rem; }
  code {
    background: var(--midground);
    color: var(--background-base);
    padding: 0.1em 0.35em;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }
  a { color: var(--midground); }
</style>
</head>
<body>
<main>
<h1>Sign-in unavailable</h1>
<p>This dashboard is bound to a non-loopback host but no authentication
providers are available.</p>
<p>Configure the bundled username/password provider or an OAuth provider.
See the <a href="https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard#authentication-gated-mode">dashboard
authentication documentation</a> for setup instructions.</p>
<p>For auth-free local use, bind to <code>127.0.0.1</code> and connect through
an SSH tunnel or Tailscale.</p>
</main>
</body>
</html>
"""


# Emitted ONLY when a ``supports_password`` provider is listed, so OAuth-only
# login pages stay script-free. Plain string (not ``str.format``): braces are
# literal. One delegated submit handler covers every form; the provider name
# comes from the form's ``data-provider`` attribute.
#
# Reverse-proxy prefix support: the script reads ``data-prefix`` from the
# ``<main>`` element (set by :func:`render_login_html`) and prepends it
# to the POST target and the post-login landing path so the login flow
# works behind ``X-Forwarded-Prefix`` proxies.
_PASSWORD_FORM_SCRIPT = """\
<script>
(function () {
  var mainEl = document.querySelector('main');
  var prefix = (mainEl && mainEl.getAttribute('data-prefix')) || '';
  function handle(form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var err = form.querySelector('.form-error');
      var btn = form.querySelector('button[type=submit]');
      if (err) { err.hidden = true; err.textContent = ''; }
      if (btn) { btn.disabled = true; }
      var body = {
        provider: form.getAttribute('data-provider') || '',
        username: (form.querySelector('input[name=username]') || {}).value || '',
        password: (form.querySelector('input[name=password]') || {}).value || '',
        next: (form.querySelector('input[name=next]') || {}).value || ''
      };
      fetch(prefix + '/auth/password-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        credentials: 'same-origin'
      }).then(function (resp) {
        if (resp.ok) {
          return resp.json().then(function (data) {
            window.location.assign((data && data.next) || (prefix + '/'));
          });
        }
        var msg = resp.status === 429
          ? 'Too many attempts. Please wait and try again.'
          : (resp.status === 401 ? 'Invalid username or password.'
                                 : 'Sign-in failed. Please try again.');
        if (err) { err.textContent = msg; err.hidden = false; }
        if (btn) { btn.disabled = false; }
      }).catch(function () {
        if (err) { err.textContent = 'Network error. Please try again.'; err.hidden = false; }
        if (btn) { btn.disabled = false; }
      });
    });
  }
  var forms = document.querySelectorAll('form.provider-form');
  for (var i = 0; i < forms.length; i++) { handle(forms[i]); }
})();
</script>
"""


def render_login_html(*, next_path: str = "", prefix: str = "") -> str:
    """Return the full HTML for ``GET /login``.

    ``next_path`` is threaded into each provider button/form so the OAuth round
    trip carries it end-to-end. The caller validates it same-origin; it is
    HTML-escaped here as defence in depth.

    ``prefix`` — when set, the path prefix from ``X-Forwarded-Prefix``
    (e.g. ``"/reign"``). Prepended to all auth URLs so the login page
    works behind a reverse proxy that mounts the dashboard at a
    sub-path. Empty string (default) means no prefix — bare-root
    deploys are unaffected.
    """
    providers = list_session_providers()
    if not providers:
        return _EMPTY_HTML
    # URL-encode then HTML-escape, matching the gate's ``_safe_next_target``
    # shape so a round-tripped value is byte-identical.
    next_qs = f"&next={html.escape(quote(next_path, safe=''), quote=True)}" if next_path else ""
    buttons = [
        _render_password_form(p, next_path, prefix=prefix)
        if getattr(p, "supports_password", False) else
        f'      <a class="provider-btn" '
        f'href="{prefix}/auth/login?provider={html.escape(p.name, quote=True)}{next_qs}">'
        f'Sign in with {html.escape(p.display_name)}</a>'
        for p in providers
    ]
    needs_password_script = any(getattr(p, "supports_password", False) for p in providers)
    html_out = _LOGIN_HTML_TEMPLATE.format(
        provider_buttons="\n".join(buttons),
        password_script=_PASSWORD_FORM_SCRIPT if needs_password_script else "",
    )
    # Inject the reverse-proxy prefix so the password-login JS can read
    # it from the <main> element's data attribute, and rewrite the font
    # URLs to stay inside the mount.  ``str.replace`` after ``str.format``
    # avoids interfering with the CSS ``{{ }}`` doubling in the template.
    return _apply_proxy_prefix(html_out, prefix)


def _apply_proxy_prefix(html_out: str, prefix: str) -> str:
    """Rewrite a rendered login-family page for a reverse-proxy sub-path.

    Two rewrites, both no-ops when *prefix* is empty (bare-root deploys are
    byte-for-byte unaffected):

    * ``<main>`` gains ``data-prefix`` so the password-login JS (a plain
      string, never ``str.format``-aware) can prepend the prefix to its
      fetch target and post-login landing.
    * ``@font-face`` ``url('/fonts/...')`` becomes ``url('<prefix>/fonts/...')``
      so the fonts load from the mount instead of the origin root (404
      behind a prefix-stripping proxy).
    """
    if not prefix:
        return html_out
    html_out = html_out.replace("<main>", f'<main data-prefix="{prefix}">', 1)
    html_out = html_out.replace("url('/fonts/", f"url('{prefix}/fonts/")
    return html_out


def render_native_provider_choice_html(
        *, providers, authorize_path: str, code_challenge: str,
        code_challenge_method: str, redirect_uri: str, state: str,
        prefix: str = "") -> str:
    """Provider picker for a native authorize request with more than one interactive provider.

    Every link re-enters ``/auth/native/authorize`` with the SAME desktop PKCE inputs plus an
    explicit ``provider``, so the choice never leaves the validated native flow. ``prefix``
    (from ``X-Forwarded-Prefix``) rewrites the template's font URLs so the page works behind
    a reverse-proxy sub-path; the buttons' ``authorize_path`` is already prefixed by the caller.
    """
    common = {"code_challenge": code_challenge, "code_challenge_method": code_challenge_method,
              "redirect_uri": redirect_uri, "state": state}
    buttons = []
    for p in providers:
        href = html.escape(f"{authorize_path}?{urlencode({**common, 'provider': p.name})}",
                           quote=True)
        buttons.append(f'      <a class="provider-btn" href="{href}">'
                       f'Sign in with {html.escape(p.display_name)}</a>')
    if not buttons:
        return _EMPTY_HTML
    return _apply_proxy_prefix(
        _LOGIN_HTML_TEMPLATE.format(
            provider_buttons="\n".join(buttons), password_script=""),
        prefix)


def _render_password_form(provider, next_path: str, *, prefix: str = "") -> str:
    """Username/password form for a ``supports_password`` provider.

    ``next_path`` rides in a hidden field (already validated by the caller,
    HTML-escaped here). The provider name is a ``data-`` attribute so the
    script does not depend on field ordering.

    ``prefix`` — reverse-proxy path prefix (e.g. ``"/reign"``); kept for
    interface parity with the other renderers (the submit handler reads
    the prefix from ``<main data-prefix>``).
    """
    pname = html.escape(provider.name, quote=True)
    plabel = html.escape(provider.display_name)
    safe_next = html.escape(next_path, quote=True) if next_path else ""
    return (
        f'      <form class="provider-form" data-provider="{pname}" '
        f'autocomplete="on">\n'
        f'        <div class="form-title">Sign in with {plabel}</div>\n'
        f'        <input type="hidden" name="next" value="{safe_next}">\n'
        f'        <label class="field">\n'
        f'          <span class="field-label">Username</span>\n'
        f'          <input class="field-input" type="text" name="username" '
        f'autocomplete="username" autocapitalize="none" '
        f'autocorrect="off" spellcheck="false" required>\n'
        f'        </label>\n'
        f'        <label class="field">\n'
        f'          <span class="field-label">Password</span>\n'
        f'          <input class="field-input" type="password" name="password" '
        f'autocomplete="current-password" required>\n'
        f'        </label>\n'
        f'        <div class="form-error" role="alert" hidden></div>\n'
        f'        <button class="provider-btn" type="submit">Sign in</button>\n'
        f'      </form>'
    )
