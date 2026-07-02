import argparse
import sys


from domain_errors import AppError
from data_loader import DirectoryLoader, ConsoleLoader, ParticleSizesData
from configuration import initialize_application
from configuration import SEPARATOR, END_OF_INPUT, CSV_PARTICLE_COLUMN_NAME, XLSX_PARTICLE_COLUMN_INDEX, INPUT_DATA_PATH, OUTPUT_DATA_PATH

def parse_args() -> argparse.Namespace:
    """Parses and returns CLI arguments."""
    parser = argparse.ArgumentParser(description="Nanoparticle size distribution analysis tool")
    parser.add_argument(
        "--source",
        choices=["console", "file"],
        default="file",
        help="Where to load particle size data from (default: file)"
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
        data_loader = ConsoleLoader(SEPARATOR, END_OF_INPUT)
    else:  # args.source == "file"
        data_loader = DirectoryLoader(INPUT_DATA_PATH, CSV_PARTICLE_COLUMN_NAME, XLSX_PARTICLE_COLUMN_INDEX)
        
    try:
        data: ParticleSizesData = data_loader.load_data()
        print_measurement_summary(data)

    except AppError as e:
        print(f"Error: {e.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()