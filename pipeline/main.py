import argparse
import sys

from dotenv import load_dotenv

from .process import EPISODES_DIR, process_episode
from .rss import fetch_episodes

sys.stdout.reconfigure(line_buffering=True)
load_dotenv()


def _is_processed(episode_id):
    return (EPISODES_DIR / f"{episode_id}.json").exists()


def cmd_list(args):
    episodes = fetch_episodes()
    for ep in episodes[:args.limit]:
        mark = "*" if _is_processed(ep["episode_id"]) else " "
        print(f" {mark} {ep['published']}  {ep['episode_id']}")
        print(f"     {ep['title']}")


def cmd_process_latest(args):
    episodes = fetch_episodes()
    if not episodes:
        print("no episodes in feed", file=sys.stderr)
        sys.exit(1)
    latest = episodes[0]
    if _is_processed(latest["episode_id"]) and not args.force:
        print(f"already processed: {latest['episode_id']} (use --force to re-process)")
        return
    process_episode(**latest)


def cmd_process_episode(args):
    episodes = fetch_episodes()
    matches = [ep for ep in episodes if ep["episode_id"] == args.episode_id]
    if not matches:
        print(f"not found in feed: {args.episode_id}", file=sys.stderr)
        sys.exit(1)
    target = matches[0]
    if _is_processed(target["episode_id"]) and not args.force:
        print(f"already processed: {target['episode_id']} (use --force to re-process)")
        return
    process_episode(**target)


def main():
    parser = argparse.ArgumentParser(prog="pipeline")
    subs = parser.add_subparsers(dest="command", required=True)

    p_list = subs.add_parser("list", help="list episodes from the RSS feed")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.set_defaults(func=cmd_list)

    p_latest = subs.add_parser("process-latest", help="process the most recent episode")
    p_latest.add_argument("--force", action="store_true",
                          help="re-process even if already done")
    p_latest.set_defaults(func=cmd_process_latest)

    p_one = subs.add_parser("process-episode", help="process a specific episode by id")
    p_one.add_argument("episode_id")
    p_one.add_argument("--force", action="store_true",
                       help="re-process even if already done")
    p_one.set_defaults(func=cmd_process_episode)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
