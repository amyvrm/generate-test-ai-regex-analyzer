import json
import os

def generate_dashboard(json_path, html_path):
    with open(json_path) as f:
        data = json.load(f)
    html = [
        '<html><head><title>VRS PCAP Test Dashboard</title>',
        '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>',
        '<style>body{font-family:sans-serif;} table{border-collapse:collapse;} th,td{padding:8px;} th{background:#f0f0f0;} tr:nth-child(even){background:#f9f9f9;} .chart-container{width:600px; margin:30px 0;}</style>',
        '</head><body>',
        '<h1>VRS PCAP Test Dashboard</h1>'
    ]
    # Table summary
    html.append('<h2>Summary Table</h2>')
    html.append('<table border="1">')
    html.append('<tr><th>TSL ID</th><th>Date</th><th>PCAPs</th><th>AI Regex TP/FN (Attack)</th><th>AI Regex TP/FN (Normal)</th><th>AI Regex File</th></tr>')
    chart_labels = []
    chart_attack_tp = []
    chart_attack_fn = []
    chart_normal_tp = []
    chart_normal_fn = []
    for tid, section in data.items():
        for r in section["recent_results"]:
            ai = r["ai_regex_stats"]
            html.append(f'<tr>')
            html.append(f'<td>{tid}</td>')
            html.append(f'<td>{r["tested_on"]}</td>')
            html.append(f'<td>{", ".join(r["tested_pcaps"])}</td>')
            html.append(f'<td>{ai["attack_pcap"]["true_positive"]}/{ai["attack_pcap"]["false_negative"]}</td>')
            html.append(f'<td>{ai["normal_pcap"]["true_positive"]}/{ai["normal_pcap"]["false_negative"]}</td>')
            html.append(f'<td><code>{r["ai_regex_file"]}</code></td>')
            html.append(f'</tr>')
            # For charting, use the most recent result per TSL ID
            if tid not in chart_labels:
                chart_labels.append(tid)
                chart_attack_tp.append(ai["attack_pcap"]["true_positive"])
                chart_attack_fn.append(ai["attack_pcap"]["false_negative"])
                chart_normal_tp.append(ai["normal_pcap"]["true_positive"])
                chart_normal_fn.append(ai["normal_pcap"]["false_negative"])
        if section.get("note"):
            html.append(f'<tr><td colspan="6"><i>{section["note"]}</i></td></tr>')
    html.append('</table>')
    # Bar chart for attack TP/FN
    html.append('<div class="chart-container"><canvas id="attackChart"></canvas></div>')
    html.append('<div class="chart-container"><canvas id="normalChart"></canvas></div>')
    html.append('<script>')
    html.append(f'const labels = {json.dumps(chart_labels)};')
    html.append(f'const attackTP = {json.dumps(chart_attack_tp)};')
    html.append(f'const attackFN = {json.dumps(chart_attack_fn)};')
    html.append(f'const normalTP = {json.dumps(chart_normal_tp)};')
    html.append(f'const normalFN = {json.dumps(chart_normal_fn)};')
    html.append('new Chart(document.getElementById("attackChart"), {'
        'type: "bar", data: {labels: labels, datasets: [ '
        '{label: "Attack TP", data: attackTP, backgroundColor: "#4caf50"}, '
        '{label: "Attack FN", data: attackFN, backgroundColor: "#f44336"} ]}, '
        'options: {responsive:true, plugins:{title:{display:true,text:"Attack PCAP True/False Positives"}}}});')
    html.append('new Chart(document.getElementById("normalChart"), {'
        'type: "bar", data: {labels: labels, datasets: [ '
        '{label: "Normal TP", data: normalTP, backgroundColor: "#2196f3"}, '
        '{label: "Normal FN", data: normalFN, backgroundColor: "#ff9800"} ]}, '
        'options: {responsive:true, plugins:{title:{display:true,text:"Normal PCAP True/False Positives"}}}});')
    html.append('</script>')
    html.append('</body></html>')
    with open(html_path, 'w') as f:
        f.write('\n'.join(html))

if __name__ == "__main__":
    json_path = os.path.join(os.path.dirname(__file__), "..", "report", "vrs-pcap-test.json")
    html_path = os.path.join(os.path.dirname(__file__), "..", "report", "pcap_test_dashboard.html")
    generate_dashboard(json_path, html_path)
    print(f"Dashboard generated at {html_path}")
