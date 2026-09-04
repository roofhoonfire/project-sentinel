from sentinel.config import load_config
from sentinel.harness import SentinelHarness


def main():
    config = load_config(
        "config.json"
    )

    harness = SentinelHarness(
        config
    )

    harness.run_forever()


if __name__ == "__main__":
    main()
