import os
import json
from datetime import datetime
import glob

def save_json_report(report, path):
    with open(path, 'w') as f:
        json.dump(report, f, indent=4)

def load_json_report(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def aggregate_reports(tsl_id, enhanced_report, summary_path):
    all_reports = load_json_report(summary_path)
    all_reports[tsl_id] = enhanced_report
    save_json_report(all_reports, summary_path)
    return all_reports

def best_reports_by_score(all_reports):
    # Accepts a list or dict of reports
    if isinstance(all_reports, list):
        reports = all_reports
    else:
        reports = list(all_reports.values())
    best_reports = {}
    for rep in reports:
        key = rep['tsl_id']
        score = (
            rep['quadrant_results']['ai_regex']['attack_pcap']['true_positive'] +
            rep['quadrant_results']['ai_regex']['normal_pcap']['true_positive']
            - rep['quadrant_results']['ai_regex']['attack_pcap']['false_negative']
            - rep['quadrant_results']['ai_regex']['normal_pcap']['false_negative']
        )
        if key not in best_reports or score > best_reports[key]['_score']:
            rep['_score'] = score
            best_reports[key] = rep
    return [best_reports[k] for k in sorted(best_reports.keys())]

def render_html_table(reports, html_path):
    with open(html_path, 'w') as f:
        f.write('<html><head><title>Regex Comparison Summary</title></head><body>\n')
        f.write('<h1>Regex Comparison Summary</h1>\n')
        f.write('<table border="1" cellpadding="5" style="border-collapse:collapse;">\n')
        f.write('<tr><th>TSL ID</th><th>Date</th><th>PCAPs</th><th>Manual Regex TP/FN</th><th>AI Regex TP/FN</th><th>Manual Regex File</th><th>AI Regex File</th><th>Comparison with Standard</th></tr>\n')
        for rep in reports:
            comp = rep['comparison_with_standard']
            comp_str = 'N/A'
            if comp['match'] is True:
                comp_str = 'Match'
            elif comp['match'] is False:
                comp_str = 'Diff: ' + '; '.join(comp['differences'])
            f.write(f'<tr>')
            f.write(f'<td>{rep["tsl_id"]}</td>')
            f.write(f'<td>{rep["tested_on"]}</td>')
            f.write(f'<td>{", ".join(rep["tested_pcaps"]) if rep["tested_pcaps"] else "-"}</td>')
            f.write(f'<td>{rep["quadrant_results"]["manual_regex"]["attack_pcap"]["true_positive"]}/'
                    f'{rep["quadrant_results"]["manual_regex"]["attack_pcap"]["false_negative"]} (attack), '
                    f'{rep["quadrant_results"]["manual_regex"]["normal_pcap"]["true_positive"]}/'
                    f'{rep["quadrant_results"]["manual_regex"]["normal_pcap"]["false_negative"]} (normal)</td>')
            f.write(f'<td>{rep["quadrant_results"]["ai_regex"]["attack_pcap"]["true_positive"]}/'
                    f'{rep["quadrant_results"]["ai_regex"]["attack_pcap"]["false_negative"]} (attack), '
                    f'{rep["quadrant_results"]["ai_regex"]["normal_pcap"]["true_positive"]}/'
                    f'{rep["quadrant_results"]["ai_regex"]["normal_pcap"]["false_negative"]} (normal)</td>')
            f.write(f'<td><code>{rep["manual_regex_path"]}</code></td>')
            f.write(f'<td><code>{rep["ai_regex_path"]}</code></td>')
            f.write(f'<td>{comp_str}</td>')
            f.write(f'</tr>\n')
        f.write('</table>\n')
        f.write('</body></html>')

def print_report_files(report_dir):
    print("Generated report files:")
    for file in glob.glob(os.path.join(report_dir, "*.json")):
        print(file)
    for file in glob.glob(os.path.join(report_dir, "*.html")):
        print(file)
    for file in glob.glob(os.path.join(report_dir, "*.txt")):
        print(file)

def aggregate_best_results(all_reports):
    """
    For each TSL ID, keep up to the best three unique test results (by stats).
    If three or more results have the same stats, keep only one and note in the report.
    Returns a dict: {tsl_id: [best_results]}
    """
    from collections import defaultdict
    import hashlib
    best_results = defaultdict(list)
    stats_seen = defaultdict(set)
    for rep in sorted(all_reports.values(), key=lambda r: r['tested_on'], reverse=True):
        tid = rep['tsl_id']
        # Use a hash of the stats as a unique key
        stats_key = hashlib.md5(json.dumps(rep['quadrant_results']['ai_regex'], sort_keys=True).encode()).hexdigest()
        if stats_key not in stats_seen[tid]:
            best_results[tid].append(rep)
            stats_seen[tid].add(stats_key)
        if len(best_results[tid]) == 3:
            break
    return best_results, stats_seen

def save_vrs_pcap_test_json(best_results, stats_seen, path):
    output = {}
    for tid, results in best_results.items():
        output[tid] = {
            "recent_results": [
                {
                    "tested_on": r["tested_on"],
                    "tested_pcaps": r["tested_pcaps"],
                    "ai_regex_stats": r["quadrant_results"]["ai_regex"],
                    "ai_regex_file": r["ai_regex_path"]
                } for r in results
            ],
            "note": "Other test reports for this TSL ID have the same stats and are omitted for brevity." if len(results) == 1 and len(stats_seen[tid]) > 1 else ""
        }
    with open(path, 'w') as f:
        json.dump(output, f, indent=4)

def save_vrs_pcap_test_html(best_results, stats_seen, path):
    with open(path, 'w') as f:
        f.write('<html><head><title>VRS PCAP Test Results</title>')
        f.write('<style>body{font-family:sans-serif;} table{border-collapse:collapse;} th,td{padding:8px;} th{background:#f0f0f0;} tr:nth-child(even){background:#f9f9f9;}</style>')
        f.write('</head><body>\n')
        f.write('<h1>VRS PCAP Test Results</h1>\n')
        for tid, results in best_results.items():
            f.write(f'<h2>TSL ID: {tid}</h2>')
            f.write('<table border="1">\n')
            f.write('<tr><th>Date</th><th>PCAPs</th><th>AI Regex TP/FN (Attack)</th><th>AI Regex TP/FN (Normal)</th><th>AI Regex File</th></tr>\n')
            for r in results:
                ai = r["quadrant_results"]["ai_regex"]
                f.write(f'<tr>')
                f.write(f'<td>{r["tested_on"]}</td>')
                f.write(f'<td>{", ".join(r["tested_pcaps"])}</td>')
                f.write(f'<td>{ai["attack_pcap"]["true_positive"]}/{ai["attack_pcap"]["false_negative"]}</td>')
                f.write(f'<td>{ai["normal_pcap"]["true_positive"]}/{ai["normal_pcap"]["false_negative"]}</td>')
                f.write(f'<td><code>{r["ai_regex_path"]}</code></td>')
                f.write(f'</tr>\n')
            f.write('</table>\n')
            if len(results) == 1 and len(stats_seen[tid]) < len(results):
                f.write('<p><i>Other test reports for this TSL ID have the same stats and are omitted for brevity.</i></p>')
        f.write('</body></html>')

# Example usage:
if __name__ == "__main__":
    report_dir = os.path.join(os.path.dirname(__file__), "..", "report")
    print_report_files(report_dir)
