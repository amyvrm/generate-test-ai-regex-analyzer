import os
import json

def compare_with_standard(tsl_id, ai_attack_results, ai_normal_results, manual_attack_results, manual_normal_results, report_folder):
    """
    Compare current results with a standard report if available.
    Returns a dict with match status, differences, and reference path.
    """
    standard_report_path = os.path.join(report_folder, f"{tsl_id}_standard_report.json")
    comparison_with_standard = {
        "match": None,
        "differences": [],
        "standard_report_reference": standard_report_path if os.path.exists(standard_report_path) else None
    }
    if os.path.exists(standard_report_path):
        with open(standard_report_path, 'r') as f:
            standard_report = json.load(f)
        diffs = []
        for regex_type in ["ai_regex", "manual_regex"]:
            for pcap_type in ["attack_pcap", "normal_pcap"]:
                for metric in ["true_positive", "false_positive", "true_negative", "false_negative"]:
                    std_val = standard_report.get("quadrant_results", {}).get(regex_type, {}).get(pcap_type, {}).get(metric)
                    cur_val = None
                    if regex_type == "ai_regex":
                        if pcap_type == "attack_pcap":
                            cur_val = ai_attack_results.get(metric)
                        else:
                            cur_val = ai_normal_results.get(metric)
                    else:
                        if pcap_type == "attack_pcap":
                            cur_val = manual_attack_results.get(metric)
                        else:
                            cur_val = manual_normal_results.get(metric)
                    if std_val is not None and cur_val is not None and std_val != cur_val:
                        diffs.append(f"{regex_type} {pcap_type} {metric}: expected {std_val}, got {cur_val}")
        comparison_with_standard["match"] = len(diffs) == 0
        comparison_with_standard["differences"] = diffs
    return comparison_with_standard
