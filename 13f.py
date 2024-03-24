import xml.etree.ElementTree as ET
import pandas as pd
import argparse
import os

def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    namespace = {'ns': 'http://www.sec.gov/edgar/document/thirteenf/informationtable'}
    data = []
    for info_table in root.findall('.//ns:infoTable', namespace):
        row = {}
        for child in info_table:
            if child.tag == '{http://www.sec.gov/edgar/document/thirteenf/informationtable}shrsOrPrnAmt':
                row['sshPrnamt'] = child.find('{http://www.sec.gov/edgar/document/thirteenf/informationtable}sshPrnamt').text
                row['sshPrnamtType'] = child.find('{http://www.sec.gov/edgar/document/thirteenf/informationtable}sshPrnamtType').text
            elif child.tag == '{http://www.sec.gov/edgar/document/thirteenf/informationtable}votingAuthority':
                row['Sole'] = child.find('{http://www.sec.gov/edgar/document/thirteenf/informationtable}Sole').text
                row['Shared'] = child.find('{http://www.sec.gov/edgar/document/thirteenf/informationtable}Shared').text
                row['None'] = child.find('{http://www.sec.gov/edgar/document/thirteenf/informationtable}None').text
            else:
                row[child.tag.split('}')[-1]] = child.text
        data.append(row)
    return pd.DataFrame(data)

def main():
    parser = argparse.ArgumentParser(description='Analyze 13F XML file')
    parser.add_argument('file_path', help='Path to the 13F XML file')
    parser.add_argument('-n', '--top-positions', type=int, default=20, help='Number of top positions to display (default: 20)')
    args = parser.parse_args()

    file_path = args.file_path
    top_n = args.top_positions

    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    df = parse_xml(file_path)
    print("DataFrame:")
    print(df)

    print("\nColumn Names:")
    print(df.columns)

    df_filtered = df[(df['putCall'] != 'Put') & (df['putCall'] != 'Call')]
    df_filtered['value'] = pd.to_numeric(df_filtered['value'], errors='coerce')

    print("\nTotal Value (excluding Put and Call):")
    print(df_filtered['value'].astype(int).sum())

    print("\nTotal Value:")
    print(df['value'].astype(int).sum())

    print("\nCount of Rows:")
    print(len(df))

    top_positions = df_filtered.nlargest(top_n, 'value')
    print(f"\nTop {top_n} Positions by Value (excluding calls and puts):")
    print(top_positions[['nameOfIssuer', 'value']])

if __name__ == '__main__':
    main()