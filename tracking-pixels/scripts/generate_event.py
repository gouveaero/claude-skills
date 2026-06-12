#!/usr/bin/env python3
"""Add a new event to a site's tracking install (idempotent).

Usage:
    python generate_event.py \\
        --site /path/to/site \\
        --tracking-json /path/to/.tracking.json \\
        --name InitiateCheckout \\
        --fire-on click \\
        --selector "[data-cta='checkout']"

Sales events (Purchase, AddPaymentInfo) are opt-in only: they normally fire on the
checkout platform (Hotmart/Eduzz/Kiwify), not the site. Adding them requires the
explicit --allow-sales-event flag, after the user confirms the site itself
processes the sale.

What it does:
    1. Validates the event name against the known EventName union.
    2. Reads .tracking.json. If the event is already there with matching fire_on/selector,
       exits 0 — no-op.
    3. Appends the event to events[] in .tracking.json (preserving formatting).
    4. Prints a concrete code snippet showing where to wire the track() call in the React
       component matching the selector (does NOT modify component code — that's a human decision).

Does NOT modify the lib/track.ts EventName union — if you're adding a brand-new event name
that's not in the union, edit lib/track.ts manually first.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KNOWN_EVENTS = {
    "PageView", "ViewContent", "Lead", "CompleteRegistration",
    "InitiateCheckout", "AddPaymentInfo", "Purchase",
    "Contact", "Schedule", "SubmitApplication", "Search", "AddToCart",
}

FIRE_ON_VALUES = {"every_route", "form_submit", "click", "load", "manual"}

# Fire on the checkout platform, not the site — see SKILL.md scope rule.
SALES_EVENTS = {"Purchase", "AddPaymentInfo"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--tracking-json", type=Path, required=True)
    parser.add_argument("--name", required=True, help="EventName, e.g. Purchase")
    parser.add_argument("--fire-on", required=True, choices=sorted(FIRE_ON_VALUES))
    parser.add_argument("--selector", default=None, help="CSS selector when fire_on is form_submit or click")
    parser.add_argument(
        "--allow-sales-event",
        action="store_true",
        help="Required to add Purchase/AddPaymentInfo — only after the user explicitly "
        "confirms the site itself processes the sale.",
    )
    args = parser.parse_args()

    if args.name in SALES_EVENTS and not args.allow_sales_event:
        print(
            f"⚠️  '{args.name}' is a sales/checkout event. On Exos client sites, purchase events\n"
            "normally fire on the checkout platform (Hotmart/Eduzz/Kiwify), NOT on the site.\n"
            "Firing it here too inflates ROAS and breaks dedup (checkout-side events carry\n"
            "different event_ids). Re-run with --allow-sales-event ONLY after the user\n"
            "explicitly confirms the site itself processes the sale.",
            file=sys.stderr,
        )
        return 2

    if args.name not in KNOWN_EVENTS:
        print(
            f"warning: '{args.name}' is not in the V1 EventName union. "
            f"Edit lib/track.ts manually to extend the union before using this event.",
            file=sys.stderr,
        )

    if not args.tracking_json.exists():
        print(f"error: {args.tracking_json} does not exist", file=sys.stderr)
        return 1

    with args.tracking_json.open() as f:
        config = json.load(f)

    events = config.setdefault("events", [])

    # Idempotency: check if this exact event already exists
    for ev in events:
        same_name = ev.get("name") == args.name
        same_fire = ev.get("fire_on") == args.fire_on
        same_sel = ev.get("selector") == args.selector
        if same_name and same_fire and same_sel:
            print(f"event '{args.name}' with same fire_on/selector already present — no-op")
            return 0

    new_entry: dict = {"name": args.name, "fire_on": args.fire_on}
    if args.selector:
        new_entry["selector"] = args.selector
    events.append(new_entry)

    with args.tracking_json.open("w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"✅ Added '{args.name}' to {args.tracking_json}")

    # Print wire-up hint
    print("\nWire it up in your component:\n")
    if args.fire_on == "form_submit":
        print(f"""  // In the component containing {args.selector}:
  import {{ track }} from '@/lib/track';

  async function onSubmit(formData) {{
    await track('{args.name}', {{
      email: formData.email,
      phone: formData.phone,
      // value/currency optional for Lead-class events
    }});
    // ... your existing submission logic
  }}""")
    elif args.fire_on == "click":
        print(f"""  // In the component containing {args.selector}:
  import {{ track }} from '@/lib/track';

  <button onClick={{() => track('{args.name}', {{ value: 99, currency: 'BRL' }})}}>
    CTA
  </button>""")
    elif args.fire_on == "every_route":
        print(f"""  // {args.name} on every route change — PixelBootstrap fires PageView on hard load
  // AND on client-side route changes (it listens for pathname changes). For other
  // route-level events, add a useEffect in your root layout that calls
  //   track('{args.name}', ...)
  // on every pathname change.""")
    elif args.fire_on == "load":
        print(f"""  // In the page that should fire {args.name} on first load:
  import {{ useEffect }} from 'react';
  import {{ track }} from '@/lib/track';

  useEffect(() => {{
    void track('{args.name}');
  }}, []);""")
    else:
        print(f"  // Fire {args.name} from wherever the business logic decides — call track('{args.name}', ...) directly.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
