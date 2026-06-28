import argparse
import sys


from domain_errors import AppError
from data_loader import ConsoleDataLoader, DirectoryCSVDataLoader, ParticleDataLoader, ParticleSizesData
from configuration import initialize_application
from configuration import SEPARATOR, END_OF_INPUT, CSV_PARTICLE_COLUMN_NAME, INPUT_DATA_PATH, OUTPUT_DATA_PATH

def parse_args() -> argparse.Namespace:
    """Parses and returns CLI arguments."""
    parser = argparse.ArgumentParser(description="Nanoparticle size distribution analysis tool")
    parser.add_argument(
        "--source",
        choices=["console", "csv"],
        default="csv",
        help="Where to load particle size data from (default: csv)"
    )
    return parser.parse_args()



def main():
    """Entry point: initialises the app, selects a data loader, and prints loaded sizes."""
    initialize_application()
    args = parse_args()

    if args.source == "console":
        data_loader = ConsoleDataLoader(SEPARATOR, END_OF_INPUT)
    elif args.source == "csv":
        data_loader = DirectoryCSVDataLoader(INPUT_DATA_PATH, CSV_PARTICLE_COLUMN_NAME)
    else:
        # unreachable — argparse enforces the choices above
        raise ValueError(f"Invalid source '{args.source}'. Valid options are 'console' or 'csv'.")
    
    try:
        data: ParticleSizesData = data_loader.load_data()

    except AppError as e:
        print(f"Error: {e.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()