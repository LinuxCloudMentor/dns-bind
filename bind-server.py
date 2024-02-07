import subprocess

def install_packages():
    subprocess.run(["yum", "-y", "install", "bind", "bind-utils"])

def get_dns_ip_address():
    dns_ip_address = input("Enter the DNS server IP address: ")
    return dns_ip_address

def configure_named(dns_ip_address):
    named_conf = f"""
options {{
        listen-on port 53 {{ 127.0.0.1; {dns_ip_address}; }};
        listen-on-v6 port 53 {{ ::1; }};
        directory       "/var/named";
        dump-file       "/var/named/data/cache_dump.db";
        statistics-file "/var/named/data/named_stats.txt";
        memstatistics-file "/var/named/data/named_mem_stats.txt";
        secroots-file   "/var/named/data/named.secroots";
        recursing-file  "/var/named/data/named.recursing";
        allow-query     {{ localhost; any; }};

        recursion yes;
        dnssec-validation yes;
        managed-keys-directory "/var/named/dynamic";
        geoip-directory "/usr/share/GeoIP";
        pid-file "/run/named/named.pid";
        session-keyfile "/run/named/session.key";
        include "/etc/crypto-policies/back-ends/bind.config";
}};

logging {{
        channel default_debug {{
                file "data/named.run";
                severity dynamic;
        }};
}};

zone "." IN {{
        type hint;
        file "named.ca";
}};

zone "ocp.local" IN {{
         type master;
         file "/var/named/ocp.local.db";
         allow-update {{ none; }};
}};


zone "168.168.192.in-addr.arpa" IN {{
          type master;
          file "/var/named/168.168.192.db";
          allow-update {{ none; }};
}};

include "/etc/named.rfc1912.zones";
include "/etc/named.root.key";
"""
    with open("/etc/named.conf", "w") as named_conf_file:
        named_conf_file.write(named_conf)

def configure_forward_zone():
    forward_zone = """
$TTL    604800
@       IN      SOA     ocp4-svc.ocp.local. admin.ocp.local. (
                  1     ; Serial
             604800     ; Refresh
              86400     ; Retry
            2419200     ; Expire
             604800     ; Negative Cache TTL
)

; name servers - NS records
    IN      NS      ocp4-svc

; name servers - A records
ocp4-svc.ocp.local.                          IN      A      192.168.168.18

; OpenShift Container Platform Cluster - A records
ocp4-bootstrap.ocp.local.                    IN      A      10.0.0.200
ocp4-cp-1.ocp.local.                         IN      A      10.0.0.201
ocp4-cp-2.ocp.local.                         IN      A      10.0.0.202
ocp4-cp-3.ocp.local.                         IN      A      10.0.0.203
ocp4-compute-1.ocp.local.                    IN      A      10.0.0.204
ocp4-compute-2.ocp.local.                    IN      A      10.0.0.205

; OpenShift internal cluster IPs - A records
api.ocp.local.                               IN    A    10.0.0.210
api-int.ocp.local.                           IN    A    10.0.0.210
*.apps.ocp.local.                            IN    A    10.0.0.210
etcd-0.ocp.local.                            IN    A    10.0.0.201
etcd-1.ocp.local.                            IN    A    10.0.0.202
etcd-2.ocp.local.                            IN    A    10.0.0.203
console-openshift-console.apps.ocp.local.    IN    A    10.0.0.210
oauth-openshift.apps.ocp.local.              IN    A    10.0.0.210

; OpenShift internal cluster IPs - SRV records
_etcd-server-ssl._tcp.ocp.local.    86400     IN    SRV     0    10    2380    etcd-0.lab
_etcd-server-ssl._tcp.ocp.local.    86400     IN    SRV     0    10    2380    etcd-1.lab
_etcd-server-ssl._tcp.ocp.local.    86400     IN    SRV     0    10    2380    etcd-2.lab
"""
    with open("/var/named/ocp.local.db", "w") as forward_zone_file:
        forward_zone_file.write(forward_zone)

def configure_reverse_zone():
    reverse_zone = """
$TTL 86400
@   IN  SOA     ocp4-svc.ocp.local. admin.ocp.local. (
    2019061800 ;Serial
    3600 ;Refresh
    1800 ;Retry
    604800 ;Expire
    86400 ;Minimum TTL
)

; name servers - NS records
    IN      NS      ocp4-svc.ocp.local.

; name servers - PTR records
18    IN    PTR    ocp4-svc.ocp.local.

; PTR Record IP address to HostName
200    IN    PTR    ocp4-bootstrap.ocp.local.
201    IN    PTR    ocp4-cp-1.ocp.local.
202    IN    PTR    ocp4-cp-2.ocp.local.
203    IN    PTR    ocp4-cp-3.ocp.local.
204    IN    PTR    ocp4-compute-1.ocp.local.
205    IN    PTR    ocp4-compute-2.ocp.local.
210    IN    PTR    api.ocp.local.
210    IN    PTR    api-int.ocp.local.
"""
    with open("/var/named/168.168.192.db", "w") as reverse_zone_file:
        reverse_zone_file.write(reverse_zone)

def restart_named():
    subprocess.run(["systemctl", "restart", "named"])
    subprocess.run(["systemctl", "enable", "named"])

def configure_firewall():
    subprocess.run(["firewall-cmd", "--permanent", "--add-port=53/udp"])
    subprocess.run(["firewall-cmd", "--reload"])

def restart_network_manager():
    subprocess.run(["systemctl", "restart", "NetworkManager"])

def main():
    install_packages()
    dns_ip_address = get_dns_ip_address()
    configure_named(dns_ip_address)
    configure_forward_zone()
    configure_reverse_zone()
    restart_named()
    configure_firewall()
    restart_network_manager()

if __name__ == "__main__":
    main()

