from filter.url_filter import deduplicate, exclude_domain_suffixes, normalize_url

def test_normalize():
    assert normalize_url("HTTPS://WWW.Example.com/a/?utm_source=x#top") == "https://example.com/a"

def test_deduplicate_scheme():
    assert len(deduplicate(["http://example.com", "https://www.example.com/"])) == 1

def test_github_family_is_excluded_without_false_suffix_match():
    urls = [
        "https://github.com/org/repo", "https://user.github.io/site",
        "https://raw.githubusercontent.com/org/repo/main/a", "https://notgithub.com/",
    ]
    assert exclude_domain_suffixes(urls, ["github.com", "github.io", "githubusercontent.com"]) == ["https://notgithub.com/"]
