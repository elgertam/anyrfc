#!/usr/bin/env python3
"""
Demonstration of improved IMAP API ergonomics with enums.

This shows the before/after of using enums vs literal strings.
"""

from anyrfc.email.imap import (
    MessageFlag,
    FetchItem,
    StoreAction,
    SearchCriteria,
    build_fetch_items,
    build_flag_list,
    build_search_criteria,
)


def demonstrate_enum_improvements():
    """Show the improved ergonomics with enums."""

    print("=" * 60)
    print("IMAP API Ergonomics: Before vs After Enums")
    print("=" * 60)

    print("\n1. SEARCH CRITERIA")
    print("Before (raw strings):")
    print('  search_cmd = "UNSEEN SINCE 1-Jan-2024 FROM gmail.com"')

    print("After (enums + builder):")
    search_cmd = build_search_criteria(SearchCriteria.UNSEEN, since="1-Jan-2024", from_="gmail.com")
    print('  search_cmd = build_search_criteria(SearchCriteria.UNSEEN, since="1-Jan-2024", from_="gmail.com")')
    print(f"  Result: {search_cmd}")

    print("\n2. FETCH ITEMS")
    print("Before (raw strings):")
    print('  fetch_items = "FLAGS UID ENVELOPE BODYSTRUCTURE"')

    print("After (enums + builder):")
    fetch_items = build_fetch_items(FetchItem.FLAGS, FetchItem.UID, FetchItem.ENVELOPE, FetchItem.BODYSTRUCTURE)
    print(
        "  fetch_items = build_fetch_items(FetchItem.FLAGS, FetchItem.UID, FetchItem.ENVELOPE, FetchItem.BODYSTRUCTURE)"
    )
    print(f"  Result: {fetch_items}")

    print("\n3. MESSAGE FLAGS")
    print("Before (raw strings):")
    print('  flags = "(\\\\Seen \\\\Flagged)"')

    print("After (enums + builder):")
    flags = build_flag_list(MessageFlag.SEEN, MessageFlag.FLAGGED)
    print("  flags = build_flag_list(MessageFlag.SEEN, MessageFlag.FLAGGED)")
    print(f"  Result: {flags}")

    print("\n4. STORE ACTIONS")
    print("Before (raw strings):")
    print('  action = "+FLAGS"  # Add flags')
    print('  action = "-FLAGS"  # Remove flags')
    print('  action = "FLAGS"   # Replace flags')

    print("After (enums):")
    print(f'  action = StoreAction.ADD.value      # "{StoreAction.ADD.value}"')
    print(f'  action = StoreAction.REMOVE.value   # "{StoreAction.REMOVE.value}"')
    print(f'  action = StoreAction.REPLACE.value  # "{StoreAction.REPLACE.value}"')

    print("\n5. COMPLEX SEARCH EXAMPLES")
    print("Before (manual string building):")
    print('  criteria = f\'UNSEEN SINCE "{date}" FROM "{sender}" SUBJECT "{subject}"\'')

    print("After (keyword arguments):")
    complex_search = build_search_criteria(
        SearchCriteria.UNSEEN, since="1-Jan-2024", from_="important@company.com", subject="Quarterly Report"
    )
    print("  criteria = build_search_criteria(")
    print("      SearchCriteria.UNSEEN,")
    print('      since="1-Jan-2024",')
    print('      from_="important@company.com",')
    print('      subject="Quarterly Report"')
    print("  )")
    print(f"  Result: {complex_search}")

    print("\n6. TYPE SAFETY BENEFITS")
    print("✅ Autocomplete: Your IDE can suggest available flags/items")
    print("✅ Type checking: mypy catches typos at development time")
    print("✅ Documentation: Enums are self-documenting")
    print("✅ Refactoring: Rename operations work across the codebase")
    print("✅ No magic strings: Compile-time error for invalid constants")

    print("\n" + "=" * 60)
    print("Summary: Enums provide better developer experience while")
    print("maintaining full RFC compliance underneath!")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_enum_improvements()
