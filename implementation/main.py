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



def print_measurement_summary(data: ParticleSizesData) -> None:
    """
    Prints a formatted table of per-source particle counts with a total row.
    """
    print("=====================================================================")
    print("Measurement counts from different images/files:")
    print()
    sorted_counts :list[tuple[str, int]] = sorted(data.counts.items())
    max_filename_length = max(len(name) for name in data.counts)
    max_filename_length = max(max_filename_length+5, 30)
    # print header
    print(f"{'File/image':<{max_filename_length}}|{'Count':>10}")
    print('-'*(max_filename_length + 11))

    for name, count in sorted_counts:
        print(f"{name:<{max_filename_length}}|{count:>10,}")
    
    # print the total count
    print('-'*(max_filename_length + 11))
    print(f"{'TOTAL':<{max_filename_length}}|{sum(data.counts.values()):>10,}")
    print('-'*(max_filename_length + 11))
    print("=====================================================================")


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
        print_measurement_summary(data)

    except AppError as e:
        print(f"Error: {e.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()