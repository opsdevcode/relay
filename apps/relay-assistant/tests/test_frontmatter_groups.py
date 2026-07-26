from portal_assistant.frontmatter import metadata_group_list, parse_frontmatter


def test_metadata_group_list_from_yaml_list():
    meta, _ = parse_frontmatter(
        """---
allowed_groups:
  - platform-team
  - relay-platform-admins
---
body
"""
    )
    assert metadata_group_list(meta, "allowed_groups") == (
        "platform-team",
        "relay-platform-admins",
    )
