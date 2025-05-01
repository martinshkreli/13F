I made this repo to allow users to analyze 13F xml files.
Just download the 13F you want to analyze from the SEC website.
The main feature of this repo is EXCLUDING options related 13F holdings, which distort holdings by inflating portfolio value when the economic exposure is far less.
I included a few 13Fs as an example.

## Prerequisites

- Python 3.x
- pandas library

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/martinshkreli/13F.git
   ```
2. Navigate to the repository:
   ```
   cd 13F
   ```
4. Install pandas or requirements.txt
   ```
   pip install -r requirements.txt
   ```
   - or if you are using nix then run:
   ```
   nix-shell
   ```
   - use this ONLY if 'nixpkgs' was not found:
       ```
       NIX_BUILD_SHELL=/bin/bash nix-shell
       ```

5. Run the program:
    ```
    python 13f.py path/to/xml/file.xml [-n TOP_POSITIONS]
    ```
    - Replace `path/to/xml/file.xml` with the path to your 13F XML file.

## Optional arguments:
### -n [TOP_POSITIONS] 
### --top-positions [TOP_POSITIONS]
- `-n TOP_POSITIONS` or `--top-positions TOP_POSITIONS`: Specify the number of top positions to display (default is 20).
##### Example:
`python 13f.py filings/13f_filing.xml -n 10`

## Output

The script will display the following information:

- DataFrame: The parsed data from the 13F filing in a pandas DataFrame format.
- Column Names: The names of the columns in the DataFrame.
- Total Value (excluding Put and Call): The total value of positions, excluding put and call options.
- Total Value: The total value of all positions.
- Count of Rows: The total number of rows in the DataFrame.
- Top Positions by Value (excluding calls and puts): The top positions by value, excluding call and put options.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
