from filter.url_filter import classify_url, deduplicate, exclude_domain_suffixes, is_public_http_url, normalize_url

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

def test_non_public_literal_urls_are_rejected():
    assert not is_public_http_url("http://localhost:3000")
    assert not is_public_http_url("http://127.0.0.1")
    assert not is_public_http_url("http://192.168.1.2")
    assert is_public_http_url("https://example.com")

def test_platform_root_is_not_a_deployment_but_subdomain_is():
    assert classify_url("https://railway.app") == "DOCUMENT"
    assert classify_url("https://my-project.railway.app") == "DEPLOYMENT_SITE"
