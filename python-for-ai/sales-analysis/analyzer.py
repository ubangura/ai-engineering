import os

import pandas as pd


def calculate_total(quantity: int, price: float) -> float:
    """Calculate total for a single item"""
    return quantity * price


def format_currency(amount: float) -> str:
    """Format number as currency"""
    return f"${amount:,.2f}"


# ---------------------------------------------------------------------
# Read Data
# ---------------------------------------------------------------------

df = pd.read_csv("data/sales.csv")
print(f"CSV Data:\n {df}\n")
print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n")

# ---------------------------------------------------------------------
# Process Data
# ---------------------------------------------------------------------

totals = []

for index, row in df.iterrows():
    total = round(calculate_total(row["quantity"], row["price"]), 2)
    totals.append(total)

df["total"] = totals


print("Sales Data:\n")
for index, row in df.iterrows():
    formatted_total = format_currency(row["total"])
    print(f"{row['product']} (x{row['quantity']}): {formatted_total}\n")

grand_total = format_currency(df["total"].sum())
print(f"Grand Total: {grand_total}")


# ---------------------------------------------------------------------
# Write Data
# ---------------------------------------------------------------------

os.makedirs("output", exist_ok=True)

df.to_json("output/sales_data.json", orient="records", indent=2)
df.to_excel("output/sales_data.xlsx", index=False)
df.to_csv("output/sales_with_totals.csv", index=False)

print("\nFiles saved:")
print("- output/sales_data.json")
print("- output/sales_data.xlsc")
print("- output/sales_with_totals.csv")
