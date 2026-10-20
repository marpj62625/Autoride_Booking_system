with open('admin_app/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

pos_start = content.find('async exportExcel() {\n            if (typeof anime')
if pos_start == -1:
    pos_start = content.find('async exportExcel()')
    # find the second occurrence if needed
    pos_start = content.find('async exportExcel()', pos_start + 10)

print("Found start at:", pos_start)

# Find end of exportExcel (before next function or end of object)
pos_end = content.find('openRecordExpenseModal()', pos_start)
if pos_end == -1:
    pos_end = content.find('renderExpensesTable(', pos_start)
print("Found next function at:", pos_end)

# Let's inspect the block between pos_start and pos_end
sub = content[pos_start:pos_end]
# find the closing brace of exportExcel
closing_brace_idx = sub.rfind('},')
if closing_brace_idx != -1:
    old_func = sub[:closing_brace_idx + 2]
    print("Found exact old_func length:", len(old_func))
else:
    print("Closing brace not found")
