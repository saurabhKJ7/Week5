monday_visitors = {"Alice", "Bob", "Charlie", "David"}
tuesday_visitors = {"Bob", "Charlie", "Eve", "Frank"}
wednesday_visitors = {"Charlie", "Eve", "George", "Alice"}

unique_visitors = monday_visitors | tuesday_visitors | wednesday_visitors
print("1. Unique Visitors Across All Days:", unique_visitors)
print("Total Unique Visitors:", len(unique_visitors))

returning_tuesday = monday_visitors & tuesday_visitors
print("\n2. Returning Visitors on Tuesday:", returning_tuesday)

new_monday = monday_visitors
new_tuesday = tuesday_visitors - monday_visitors
new_wednesday = wednesday_visitors - (monday_visitors | tuesday_visitors)
print("\n3. New Visitors Each Day:")
print("  Monday:", new_monday)
print("  Tuesday:", new_tuesday)
print("  Wednesday:", new_wednesday)

loyal_visitors = monday_visitors & tuesday_visitors & wednesday_visitors
print("\n4. Loyal Visitors (all three days):", loyal_visitors)

overlap_monday_tuesday = monday_visitors & tuesday_visitors
overlap_tuesday_wednesday = tuesday_visitors & wednesday_visitors
overlap_monday_wednesday = monday_visitors & wednesday_visitors

print("\n5. Daily Visitor Overlap Analysis:")
print("  Monday & Tuesday:", overlap_monday_tuesday)
print("  Tuesday & Wednesday:", overlap_tuesday_wednesday)
print("  Monday & Wednesday:", overlap_monday_wednesday)
