import re

def load_regex_from_file(pattern_file):
    """Load regex patterns from an XML-like structure in the file."""
    regex_patterns = []
    with open(pattern_file, 'r') as f:
        content = f.read().strip()
        matches = re.findall(r"<pstring>(.*?)</pstring>", content, re.DOTALL)
        if matches:
            regex_patterns = [match.strip() for match in matches]
        else:
            # fallback: treat each line as a regex if no XML tags
            regex_patterns = [line.strip() for line in content.splitlines() if line.strip()]
    return regex_patterns

def apply_regex_to_packets(packets, regex_patterns, is_http_packet_fn):
    """
    Apply regex patterns to packets in memory and evaluate matches.
    Returns a dictionary with match results and logs unmatched packets.
    """
    results = {"true_positive": 0, "false_positive": 0, "true_negative": 0, "false_negative": 0}
    unmatched_packets = []
    for packet in packets:
        if not is_http_packet_fn(packet):
            continue  # Skip non-HTTP packets
        packet_str = str(packet)
        matched = False
        for pattern in regex_patterns:
            try:
                compiled_regex = re.compile(pattern)
                if compiled_regex.search(packet_str):
                    matched = True
                    results["true_positive"] += 1
                    break
            except re.error:
                continue  # skip invalid regex
        if not matched:
            results["false_negative"] += 1
            unmatched_packets.append(packet_str)
    return results
