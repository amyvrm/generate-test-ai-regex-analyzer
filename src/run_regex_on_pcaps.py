# -*- coding: utf-8 -*-
# This script loads PCAP files from a specified folder structure, applies regex patterns
# to the packets, and generates a report in JSON format.
# It uses Scapy for packet manipulation and regex for pattern matching.
# The script is designed to work with a specific folder structure where PCAP files are organized
# by TSL IDs. Each TSL ID corresponds to a subfolder containing PCAP files.
# The script also includes logging functionality to track the loading of PCAP files,
# regex pattern application, and report generation.

# The script should ask user to provide tsl_id
# and then it should check and load the pcaps/<tsl_id>.pcap files
# then apply the regex kept in file report/ai_regex/<tsl_id>.txt
# In report keep xml regex pattern match result

import logging
import os
import re
import json
import argparse
from scapy.all import rdpcap
from datetime import datetime, timezone
from scapy.layers.inet import IP, TCP
from scapy.layers.http import HTTPRequest, HTTPResponse
from scapy.layers.dns import DNS
from scapy.layers.l2 import Ether
from scapy.layers.inet6 import IPv6
from scapy.all import conf
# from sklearn.ensemble import RandomForestClassifier
# import numpy as np
import scapy.all as scapy
from pcap_loader import load_pcaps_by_tsl, is_http_packet
from regex_utils import load_regex_from_file, apply_regex_to_packets
from report_utils import save_json_report, aggregate_reports, best_reports_by_score, render_html_table, print_report_files
from compare import compare_with_standard

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler
file_handler = logging.FileHandler('load_pcap_apply_regex.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Create a stream handler for console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class RegexPcapTester:
    def __init__(self, config):
        self.pcap_folder = config["pcap_folder"]
        self.ai_pattern_folder = config["ai_regex_path"]
        self.report_folder = config["report_folder"]

    def process_tsl(self, tsl_id):
        attack_pcap_path = os.path.join(self.pcap_folder, tsl_id, "attack.pcap")
        normal_pcap_path = os.path.join(self.pcap_folder, tsl_id, "normal.pcap")
        ai_pattern_file = os.path.join(self.ai_pattern_folder, f"{tsl_id}.txt")
        output_report_path = os.path.join(self.report_folder, f"{tsl_id}_regex_comparison_report.json")
        html_path = os.path.join(self.report_folder, "regex_comparison_summary_view.html")

        # Skip if the AI regex file does not exist
        if not os.path.exists(ai_pattern_file):
            logger.error(f"AI regex file not found for {tsl_id}: {ai_pattern_file}, skipping.")
            return

        # Load regex patterns
        ai_regex_patterns = load_regex_from_file(ai_pattern_file)

        # Load PCAPs
        attack_packets = []
        normal_packets = []
        if os.path.exists(attack_pcap_path):
            attack_packets = load_pcaps_by_tsl(self.pcap_folder, tsl_id)[0].get(tsl_id, [[]])[0]
        if os.path.exists(normal_pcap_path):
            normal_packets = load_pcaps_by_tsl(self.pcap_folder, tsl_id)[0].get(tsl_id, [[]])[0]

        # Apply regex
        ai_attack_results = apply_regex_to_packets(attack_packets, ai_regex_patterns, is_http_packet)
        ai_normal_results = apply_regex_to_packets(normal_packets, ai_regex_patterns, is_http_packet)

        now_iso = datetime.now(timezone.utc).isoformat()
        tested_pcaps = []
        if os.path.exists(attack_pcap_path):
            tested_pcaps.append(os.path.basename(attack_pcap_path))
        if os.path.exists(normal_pcap_path):
            tested_pcaps.append(os.path.basename(normal_pcap_path))
        ai_regex_path = os.path.abspath(ai_pattern_file)

        # Context for report
        context = (
            f"Context: The main agenda is to test and improve AI Regex performance. "
            f"This report evaluates the effectiveness of AI-generated regex patterns for detecting relevant packets in the provided PCAP files. "
            f"The AI regex file contains {len(ai_regex_patterns)} patterns, all of which were matched against the PCAP data."
        )
        user_friendly_summary = (
            f"TSL: {tsl_id} | Date: {now_iso} | PCAPs: {', '.join(tested_pcaps)}\n"
            f"{context}\n"
            f"AI Regex: attack TP={ai_attack_results['true_positive']}, FN={ai_attack_results['false_negative']}\n"
            f"AI Regex file ({len(ai_regex_patterns)} patterns): {ai_regex_path}\n"
            f"See quadrant and pattern details in JSON report."
        )

        enhanced_report = {
            "tsl_id": tsl_id,
            "tested_on": now_iso,
            "tested_pcaps": tested_pcaps,
            "ai_regex_path": ai_regex_path,
            "quadrant_results": {
                "ai_regex": {
                    "attack_pcap": ai_attack_results,
                    "normal_pcap": ai_normal_results
                }
            },
            "ai_regex_patterns": ai_regex_patterns,
            "context": context,
            "user_friendly_summary": user_friendly_summary
        }
        save_json_report(enhanced_report, output_report_path)
        best = best_reports_by_score([enhanced_report])
        # --- Improved HTML report with better layout ---
        def improved_html_table(reports, html_path):
            with open(html_path, 'w') as f:
                f.write('<html><head><title>Regex Comparison Summary</title>')
                f.write('<style>body{font-family:sans-serif;} table{border-collapse:collapse;} th,td{padding:8px;} th{background:#f0f0f0;} tr:nth-child(even){background:#f9f9f9;} .percent{font-weight:bold;color:#0070c0;}</style>')
                f.write('</head><body>\n')
                f.write('<h1>Regex Comparison Summary</h1>\n')
                f.write('<p><b>Main agenda:</b> Test and improve <span style="color:#0070c0;">AI Regex</span>.</p>')
                f.write('<table border="1">\n')
                f.write('<tr><th>TSL ID</th><th>Date</th><th>PCAPs</th><th>AI Regex TP/FN</th><th>AI Regex File</th></tr>\n')
                for rep in reports:
                    f.write(f'<tr>')
                    f.write(f'<td>{rep["tsl_id"]}</td>')
                    f.write(f'<td>{rep["tested_on"]}</td>')
                    f.write(f'<td>{", ".join(rep["tested_pcaps"]) if rep["tested_pcaps"] else "-"}</td>')
                    f.write(f'<td>{rep["quadrant_results"]["ai_regex"]["attack_pcap"]["true_positive"]}/'
                            f'{rep["quadrant_results"]["ai_regex"]["attack_pcap"]["false_negative"]} (attack), '
                            f'{rep["quadrant_results"]["ai_regex"]["normal_pcap"]["true_positive"]}/'
                            f'{rep["quadrant_results"]["ai_regex"]["normal_pcap"]["false_negative"]} (normal)</td>')
                    f.write(f'<td><code>{rep["ai_regex_path"]}</code></td>')
                    f.write(f'</tr>\n')
                f.write('</table>\n')
                f.write('<br><details><summary>Show Context</summary><pre>')
                for rep in reports:
                    f.write(f'{rep["tsl_id"]}: {rep.get("context","-")}\n')
                f.write('</pre></details>')
                f.write('</body></html>')
        improved_html_table(best, html_path)
        print(f"Report for {tsl_id} generated and aggregated.")

class AgenticRegexTester(RegexPcapTester):
    def agentic_loop(self, tsl_id, max_iterations=5, improvement_threshold=0.99):
        best_score = 0
        best_report = None
        for iteration in range(max_iterations):
            print(f"Agentic iteration {iteration+1} for {tsl_id}")
            self.process_tsl(tsl_id)
            # Load latest report
            report_path = os.path.join(self.report_folder, f"{tsl_id}_regex_comparison_report.json")
            with open(report_path) as f:
                report = json.load(f)
            ai_score = report.get("ai_attack_percent_of_dv", 0)
            print(f"AI Regex detection rate: {ai_score}% (iteration {iteration+1})")
            if ai_score > best_score:
                best_score = ai_score
                best_report = report
            # Stopping criteria
            if ai_score >= improvement_threshold * 100:
                print("Desired performance reached. Stopping agentic loop.")
                break
            # --- Placeholder for AI regex improvement step ---
            print("Simulating AI regex improvement (replace with LLM/optimizer call)...")
            # Here you would call an LLM or optimizer to update the AI regex file
            # For now, just simulate a change or prompt the user
            # Optionally, implement logic to update the AI regex file here
            import time
            time.sleep(1)
        print(f"Best AI Regex detection rate achieved: {best_score}%")
        # Optionally, save or report best_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Agentic PCAP Regex Tester')
    parser.add_argument('--tsl_id', required=True, help='TSL ID(s) to test (comma-separated for multiple)')
    parser.add_argument('--config_file', default='config/config.json', help='Config file path')
    parser.add_argument('--agentic', action='store_true', help='Run in agentic (autonomous improvement) mode')
    args = parser.parse_args()
    with open(args.config_file) as f:
        config = json.load(f)
    tsl_ids = [tid.strip() for tid in args.tsl_id.split(',') if tid.strip()]
    # Only keep TSLs with an existing ai_regex file
    valid_tsl_ids = []
    for tsl_id in tsl_ids:
        ai_pattern_file = os.path.join(config["ai_regex_path"], f"{tsl_id}.txt")
        if os.path.exists(ai_pattern_file):
            valid_tsl_ids.append(tsl_id)
        else:
            logger.error(f"Skipping {tsl_id}: missing AI regex file {ai_pattern_file}")
    if args.agentic:
        tester = AgenticRegexTester(config)
        for tsl_id in valid_tsl_ids:
            tester.agentic_loop(tsl_id)
    else:
        tester = RegexPcapTester(config)
        for tsl_id in valid_tsl_ids:
            tester.process_tsl(tsl_id)
        # Only generate the new required report files
        from report_utils import aggregate_best_results, save_vrs_pcap_test_json, save_vrs_pcap_test_html
        vrs_json_path = os.path.join(config["report_folder"], "vrs-pcap-test.json")
        vrs_html_path = os.path.join(config["report_folder"], "vrs-pcap-test.html")
        # Collect all per-TSL reports
        all_reports = {}
        for file in os.listdir(config["report_folder"]):
            if file.endswith("_regex_comparison_report.json"):
                with open(os.path.join(config["report_folder"], file)) as f:
                    rep = json.load(f)
                    all_reports[rep["tsl_id"]] = rep
        best_results, stats_seen = aggregate_best_results(all_reports)
        save_vrs_pcap_test_json(best_results, stats_seen, vrs_json_path)
        save_vrs_pcap_test_html(best_results, stats_seen, vrs_html_path)
        print(f"Generated {vrs_json_path} and {vrs_html_path}")
        print("Done.")