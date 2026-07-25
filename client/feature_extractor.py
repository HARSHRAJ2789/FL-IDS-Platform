import time
import numpy as np
import pandas as pd
from collections import defaultdict
from scapy.all import sniff, IP, TCP, UDP, ICMP
import logging

class PacketFeatureExtractor:
    def __init__(self, interface=None):
        self.interface = interface
        self.num_features = 196
        
    def capture_flows(self, duration_seconds):
        logging.info(f"Capturing packets on interface {self.interface} for {duration_seconds} seconds...")
        # Capture packets
        packets = sniff(iface=self.interface, timeout=duration_seconds)
        
        # Group by flow (5-tuple)
        flows = defaultdict(list)
        for pkt in packets:
            if IP in pkt:
                src = pkt[IP].src
                dst = pkt[IP].dst
                proto = pkt[IP].proto
                sport = 0
                dport = 0
                if TCP in pkt:
                    sport = pkt[TCP].sport
                    dport = pkt[TCP].dport
                elif UDP in pkt:
                    sport = pkt[UDP].sport
                    dport = pkt[UDP].dport
                
                flow_key = (src, dst, sport, dport, proto)
                flows[flow_key].append(pkt)
                
        features_list = self.extract_flow_features(flows)
        
        if len(features_list) == 0:
            # return empty df
            columns = [f'feat_{i}' for i in range(self.num_features)] + ['label']
            return pd.DataFrame(columns=columns)
            
        # Create DataFrame
        columns = [f'feat_{i}' for i in range(self.num_features)]
        df = pd.DataFrame(features_list, columns=columns)
        df['label'] = 0  # Default label, to be predicted
        return df

    def extract_flow_features(self, flows):
        features_list = []
        
        for flow_key, pkts in flows.items():
            if not pkts:
                continue
            
            src, dst, sport, dport, proto = flow_key
            
            # Basic features
            timestamps = [float(p.time) for p in pkts]
            dur = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0.0001
            
            # Proto mapping (TCP=6, UDP=17, ICMP=1)
            # scapy already provides this in pkt[IP].proto
            
            spkts = len([p for p in pkts if p[IP].src == src])
            dpkts = len(pkts) - spkts
            
            sbytes = sum([len(p) for p in pkts if p[IP].src == src])
            dbytes = sum([len(p) for p in pkts if p[IP].src != src])
            
            rate = len(pkts) / dur if dur > 0 else 0
            
            sttl = pkts[0][IP].ttl if spkts > 0 and IP in pkts[0] else 0
            
            # find first response packet for dttl
            dttl = 0
            for p in pkts:
                if p[IP].src != src and IP in p:
                    dttl = p[IP].ttl
                    break
                    
            sload = (sbytes * 8) / dur if dur > 0 else 0
            dload = (dbytes * 8) / dur if dur > 0 else 0
            
            # Just rough approximations for others to fit UNSW-NB15 format
            sloss = spkts // 10  # proxy
            dloss = dpkts // 10
            
            sinpkt = dur / spkts if spkts > 0 else 0
            dinpkt = dur / dpkts if dpkts > 0 else 0
            
            sjit = sinpkt * 0.1
            djit = dinpkt * 0.1
            
            swin = 0
            dwin = 0
            stcpb = 0
            dtcpb = 0
            if TCP in pkts[0]:
                swin = pkts[0][TCP].window
                stcpb = pkts[0][TCP].seq
            for p in pkts:
                if p[IP].src != src and TCP in p:
                    dwin = p[TCP].window
                    dtcpb = p[TCP].seq
                    break
                    
            smean = sbytes / spkts if spkts > 0 else 0
            dmean = dbytes / dpkts if dpkts > 0 else 0
            
            # Fill the rest with 0 as specified
            trans_depth = 0
            response_body_len = 0
            ct_srv_src = 1
            ct_state_ttl = 1
            ct_dst_ltm = 1
            ct_src_dport_ltm = 1
            ct_dst_sport_ltm = 1
            ct_dst_src_ltm = 1
            is_ftp_login = 0
            ct_ftp_cmd = 0
            ct_flw_http_mthd = 0
            ct_src_ltm = 1
            ct_srv_dst = 1
            is_sm_ips_ports = 1 if src == dst and sport == dport else 0
            
            extracted = [
                dur, proto, spkts, dpkts, sbytes, dbytes, rate, sttl, dttl, 
                sload, dload, sloss, dloss, sinpkt, dinpkt, sjit, djit, swin, 
                dwin, stcpb, dtcpb, smean, dmean, trans_depth, response_body_len, 
                ct_srv_src, ct_state_ttl, ct_dst_ltm, ct_src_dport_ltm, 
                ct_dst_sport_ltm, ct_dst_src_ltm, is_ftp_login, ct_ftp_cmd, 
                ct_flw_http_mthd, ct_src_ltm, ct_srv_dst, is_sm_ips_ports
            ]
            
            # Pad to 196
            feature_vector = extracted + [0.0] * (self.num_features - len(extracted))
            features_list.append(feature_vector)
            
        return np.array(features_list)

    def get_label_from_prediction(self, features, model):
        # Predict using model
        if len(features) == 0:
            return np.array([])
        
        preds = model.predict(features, verbose=0)
        labels = (preds > 0.5).astype(int).flatten()
        return labels
