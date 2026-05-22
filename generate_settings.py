"""Generate settings.yml from upstream SearXNG defaults.

Called during install to produce a Windows-optimized settings.yml
with all sensible engines enabled.

Usage:
    python generate_settings.py [output]
"""

import os
import sys
import secrets
import yaml

UPSTREAM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "searx", "searx", "settings.yml")

# Engines to always skip
SKIP = {
    # Tor-only (require Tor)
    "ahmia", "torch",
    # Need API keys
    "tineye", "flickr_api",
    # Broken / inactive upstream
    "ebay", "findthatmeme", "1x", "fdroid", "fyyd", "geizhals",
    "searchmysite", "senscritique", "mwmbl", "selfhst",
    # Regional / niche that cause issues
    "baidu", "baidu images", "bilibili", "niconico", "iqiyi", "naver",
    "naver images", "naver news", "naver videos", "sogou", "sogou images",
    "sogou videos", "sogou wechat", "yahoo", "yandex", "yandex images",
    "yandex music", "seznam", "qwant", "qwant news", "qwant images",
    "qwant videos", "presearch", "presearch images", "presearch videos",
    "presearch news", "wiby", "mojeks", "mojeks images", "mojeks news",
    "erowid", "bpb", "chinaso news", "chinaso images", "chinaso videos",
    "360search", "360search videos", "9gag", "acfun", "aol", "aol images",
    "aol videos", "deezer", "destatis", "encyclosearch", "fynd",
    "il post", "tagesschau", "duden", "wozikon.de synonyme",
    "wikimini", "marginalia", "crowdview",
    "apple maps", "duckduckgo weather",
    # Deprecated/legacy
    "kickass", "piratebay", "solidtorrents", "bt4g",
    # Piracy / copyright-infringing
    "1337x", "annas archive", "btdigg", "library genesis", "nyaa", "z-library",
}

# Engines to enable even if upstream has them disabled
FORCE_ENABLE = {
    # Popular general
    "bing", "bing images", "bing news", "bing videos",
    "youtube", "dailymotion", "vimeo",
    "reddit", "imgur",
    "imdb", "tmdb", "rottentomatoes", "steam",
    # IT/developer
    "gitlab", "npm", "crates.io", "hex", "rubygems", "pub.dev",
    "microsoft learn", "hackernews", "lobste.rs", "huggingface",
    "huggingface datasets", "huggingface spaces",
    "repology", "lib.rs", "sourcehut", "pkg.go.dev",
    "ollama",
    # Science
    "openalex", "crossref",
    # Maps
    "openstreetmap",
    # Images
    "pixabay images", "pixabay videos", "artstation", "imgur",
    # Videos
    "odysee", "peertube", "rumble",
    # News
    "reuters", "wikinews",
    # Dictionaries
    "dictzone", "jisho",
    # File search
    "openrepos",
    # Q&A
    "discuss.python", "caddy.community", "pi-hole.community",
}

# Engines to explicitly disable
EXPLICIT_DISABLE = {
    # Tor-only
    "ahmia", "torch",
    # Inactive upstream
    "ebay",
    # Need API keys
    "tineye", "flickr_api",
}


def main():
    if not os.path.isfile(UPSTREAM):
        print(f"ERROR: upstream settings not found at {UPSTREAM}", file=sys.stderr)
        sys.exit(1)

    with open(UPSTREAM) as f:
        upstream = yaml.safe_load(f)

    # Start with defaults
    settings = {}
    for key, value in upstream.items():
        if key not in ("engines", "outgoing", "general", "search", "ui", "server",
                        "preferences", "enabled_plugins", "categories_as",
                        "default_locale", "locales"):
            settings[key] = value

    settings["use_default_settings"] = True

    # Windows-specific overrides
    settings["server"] = {
        "port": 8888,
        "bind_address": "127.0.0.1",
        "secret_key": secrets.token_hex(32),
        "limit_request_field_size": 8192,
        "image_proxy": False,
        "limiter": False,
    }

    settings["search"] = {
        "safe_search": 0,
        "default_lang": "auto",
        "formats": ["html", "json"],
    }

    settings["ui"] = {
        "static_use_hash": True,
        "default_theme": "simple",
        "theme_args": {"simple_style": "auto"},
    }

    settings["general"] = {
        "debug": False,
        "instance_name": "SearXNG (Windows)",
        "public_instance": False,
    }

    settings["outgoing"] = {
        "request_timeout": 3.0,
        "enable_http2": True,
        "pool_maxsize": 20,
    }

    # Process engines from upstream (deduplicate by name)
    upstream_engines = upstream.get("engines", [])
    seen = set()
    engine_list = []
    for eng in upstream_engines:
        name = eng.get("name", "")
        if not name or name in seen:
            continue
        seen.add(name)

        # Skip engines we never want (Tor-only, broken, inactive, etc.)
        if name in SKIP:
            continue

        cats = eng.get("categories", [])
        if not cats:
            cats = ["general"]

        # Determine enabled state
        disabled = eng.get("disabled", False) or eng.get("inactive", False)

        # Force enable desired engines
        if name in FORCE_ENABLE:
            disabled = False

        # Skip disabled engines that aren't forced on
        if disabled:
            continue

        # Build engine dict (keep upstream config, override disabled)
        engine = dict(eng)
        engine["disabled"] = False
        engine_list.append(engine)

    settings["engines"] = engine_list

    # Write output
    output = sys.argv[1] if len(sys.argv) > 1 else "settings.yml"
    with open(output, "w", encoding="utf-8") as f:
        yaml.dump(settings, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True, width=120)

    print(f"Generated {output} with {len(engine_list)} engines enabled.")


if __name__ == "__main__":
    main()
