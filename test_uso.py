"""
Test manual / demostración de la API de alto nivel.

$ python tests/test_uso.py
"""
from pprint import pprint
from dotenv import load_dotenv
import os

import vtfree.log
from vtfree import VTClient
from vtfree.contrib import (
    set_default_client,
    check_urls_in_vt,
    check_ips_in_vt,
    check_domains_in_vt,
    check_hashes_in_vt,
)

# --- preparación ------------------------------------------------------ #
load_dotenv()
vtfree.log.configure(level=20)  # INFO

api_keys = [k for k in os.getenv("VT_KEYS", "").split(",") if k]
client = VTClient(api_keys, validate=True)

set_default_client(client)  # ahora los wrappers ya funcionan

# --- IOCs de ejemplo --------------------------------------------------- #
urls = [
    "http://homespottersf.com/sm/googledocs1/index.html",
    "https://undec-ab94.djuleircendku.workers.dev/b96043f6-39ae-43f3-aef7-d1371cf249e8",
]
ips = ["66.240.205.34"]
domains = ["karasserybank.com", "iownyour.biz"]
hashes = ["e0c0cbc50a9ed4d01a176497c8dba913cbbba515ea701a67ef00dcb7c8a84368"]

# --- llamadas ---------------------------------------------------------- #
results = []
results += check_urls_in_vt(urls)
results += check_ips_in_vt(ips)
results += check_domains_in_vt(domains)
results += check_hashes_in_vt(hashes)

# --- salida ------------------------------------------------------------ #
for r in results:
    pprint(r)

print("\nSnapshot de claves:")
for k in client.key_status():
    pprint(k)
