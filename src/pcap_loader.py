import os
from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP
from scapy.layers.http import HTTPRequest, HTTPResponse
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import Ether

def is_http_packet(packet):
    """Check if the packet is HTTP."""
    return (packet.haslayer(HTTPRequest) or packet.haslayer(HTTPResponse)) and \
           (packet.haslayer(IP) or packet.haslayer(IPv6)) and \
           (packet.haslayer(TCP) or packet.haslayer(Ether))

def load_pcaps_by_tsl(pcap_folder, tsl_id=None):
    """
    Load PCAPs grouped by TSL ID from the specified folder.
    Each subfolder in the PCAP folder corresponds to a TSL ID.
    Function accepts the PCAP folder path and an optional TSL ID to filter specific subfolder.
    Returns a dict {tsl_id: [list of HTTP packets]} and a list of loaded file paths.
    """
    tsl_pcaps = {}
    loaded_files = []
    if tsl_id:
        subfolder_path = os.path.join(pcap_folder, tsl_id)
        if os.path.isdir(subfolder_path):
            tsl_pcaps[tsl_id] = []
            for file in os.listdir(subfolder_path):
                if file.endswith(".pcap"):
                    pcap_path = os.path.join(subfolder_path, file)
                    packets = rdpcap(pcap_path)
                    http_packets = [pkt for pkt in packets if is_http_packet(pkt)]
                    if http_packets:
                        tsl_pcaps[tsl_id].append(http_packets)
                        loaded_files.append(pcap_path)
            if not tsl_pcaps[tsl_id]:
                del tsl_pcaps[tsl_id]
    else:
        for root, dirs, files in os.walk(pcap_folder):
            for subfolder in dirs:
                subfolder_path = os.path.join(root, subfolder)
                if os.path.isdir(subfolder_path):
                    tsl_pcaps[subfolder] = []
                    for file in os.listdir(subfolder_path):
                        if file.endswith(".pcap"):
                            pcap_path = os.path.join(subfolder_path, file)
                            packets = rdpcap(pcap_path)
                            http_packets = [pkt for pkt in packets if is_http_packet(pkt)]
                            if http_packets:
                                tsl_pcaps[subfolder].append(http_packets)
                                loaded_files.append(pcap_path)
                    if not tsl_pcaps[subfolder]:
                        del tsl_pcaps[subfolder]
    return tsl_pcaps, loaded_files
