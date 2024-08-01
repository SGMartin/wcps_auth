import argparse
import asyncio
from wcps_auth.main import main
from wcps_auth import __version__

def run():
    parser = argparse.ArgumentParser(description="WCPS Authentication server")

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    # Run the asyncio main function
    asyncio.run(main())

if __name__ == "__main__":
    run()
