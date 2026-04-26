import csv

header = None
date_idx = 30
symbol_idx = 9
amount_idx = 45
trade_id_idx = 34
transaction_id_idx = 49

seen = set()
all_records = []
with open('/Volumes/Extent/Users/chengjunsen/Downloads/U10368030_U10368030_20250425_20260424_AF_NA_3542138e595283a12e5b6cf94498eb88.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        if row and row[0] == 'DATA' and row[1] == 'STFU':
            if len(row) > max(date_idx, symbol_idx, amount_idx, transaction_id_idx):
                activity_idx = 32
                if row[activity_idx] == 'DIV':
                    date = row[date_idx]
                    if date.startswith('2026'):
                        transaction_id = row[transaction_id_idx]
                        key = transaction_id
                        if key not in seen:
                            seen.add(key)
                            try:
                                amt = float(row[amount_idx])
                                all_records.append((date, row[symbol_idx], amt, transaction_id))
                            except:
                                pass

print("All 2026 DIV records (deduped by TransactionID):")
for date, sym, amt, tid in sorted(all_records):
    print(f"  {date} {sym:8} {amt:9.2f}  TxnID={tid}")

print(f"\nTotal records: {len(all_records)}")
print(f"Total amount: {sum(r[2] for r in all_records):.2f}")