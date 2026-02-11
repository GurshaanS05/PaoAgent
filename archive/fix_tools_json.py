import re

input_file = "tools.json"
output_file = "tools_fixed.json"

with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# Remove all newlines and spaces before/after brackets for easier processing
content = re.sub(r'\[\s*', '[', content)
content = re.sub(r'\s*\]', ']', content)

# Find all objects in the file (anything between { ... })
objects = re.findall(r'\{.*?\}(?=,?\s*[\]\[]|$)', content, re.DOTALL)

# Join all objects with commas and wrap in a single array
fixed_json = '[\n' + ',\n'.join(objects) + '\n]\n'

with open(output_file, "w", encoding="utf-8") as f:
    f.write(fixed_json)

print(f"Fixed JSON written to {output_file}")