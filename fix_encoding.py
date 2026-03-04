# Fix encoding issues in paper - byte-level replacement

with open(r'E:\Ace\Presume_competence\PAPER_FINAL.md', 'rb') as f:
    content = f.read()

# Fix delta mojibake
bad_delta = b'\xc3\x8e\xe2\x80\x9d'
good_delta = b'\xce\x94'  # Δ in UTF-8

content = content.replace(bad_delta, good_delta)

with open(r'E:\Ace\Presume_competence\PAPER_FINAL.md', 'wb') as f:
    f.write(content)

print('Fixed delta encoding')

# Verify
with open(r'E:\Ace\Presume_competence\PAPER_FINAL.md', 'rb') as f:
    lines = f.readlines()
    print('Line 238:', lines[237])
