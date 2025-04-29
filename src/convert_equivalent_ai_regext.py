import re
import os

def convert_to_equivalent_format(input_file, output_file):
    """
    Converts regex patterns from a simplified format to the equivalent structured format.
    """
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            line = line.strip()
            if line.startswith("ip.saddr"):
                outfile.write("<ip.saddr>\n  <regex offset=\"0\" depth=\"-1\" nocase=\"0\"/>\n  <pstring>.*</pstring>\n</ip.saddr>\n")
            elif line.startswith("ip.daddr"):
                outfile.write("<ip.daddr>\n  <regex offset=\"0\" depth=\"-1\" nocase=\"0\"/>\n  <pstring>.*</pstring>\n</ip.daddr>\n")
            elif line.startswith("tcp.sport"):
                outfile.write("<tcp.sport>\n  <regex offset=\"0\" depth=\"-1\" nocase=\"0\"/>\n  <pstring>^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$</pstring>\n</tcp.sport>\n")
            elif line.startswith("tcp.dport"):
                outfile.write("<tcp.dport>\n  <regex offset=\"0\" depth=\"-1\" nocase=\"0\"/>\n  <pstring>^(80|8080)$</pstring>\n</tcp.dport>\n")
            elif line.startswith("tcp.established"):
                outfile.write("<tcp.established>\n  <strmatch/>\n  <pstring>true</pstring>\n</tcp.established>\n")
            elif line.startswith("tcp.flags"):
                outfile.write("<tcp.flags>\n  <regex offset=\"0\" depth=\"-1\" nocase=\"0\"/>\n  <pstring>A \\+</pstring>\n</tcp.flags>\n")
            elif line.startswith("http.method"):
                outfile.write("<http.method>\n  <strmatch/>\n  <pstring>POST</pstring>\n</http.method>\n")
            elif line.startswith("http.uri"):
                outfile.write("<http.uri>\n  <regex offset=\"0\" depth=\"-1\" nocase=\"0\"/>\n  <pstring>[\\\\/]HNAP1[\\\\/]</pstring>\n</http.uri>\n")
            elif line.startswith("payload ~ {<SetSysEmailSettings"):
                outfile.write("<payload>\n  <regex offset=\"0\" depth=\"-1\" nocase=\"0\"/>\n  <pstring><SetSysEmailSettings</pstring>\n</payload>\n")
            elif line.startswith("payload ~ {<EmailFrom"):
                outfile.write("<payload>\n  <regex offset=\"0\" depth=\"-1\" nocase=\"0\"/>\n  <pstring><EmailFrom>[^<]{0,100}[\\x24\\x26\\x3b\\x60\\x7c]</pstring>\n</payload>\n")
            else:
                # Ignore lines that don't match any known pattern
                continue

def main():
    input_file = "report/ai_regex/TSL20230504-07-wiki.txt"
    output_file = "report/ai_regex/TSL20230504-07-converted.txt"
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist.")
        return
    
    convert_to_equivalent_format(input_file, output_file)
    print(f"Converted regex patterns saved to {output_file}")

if __name__ == "__main__":
    main()
