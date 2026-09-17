from collector.github_collector import deployment_urls


def test_only_deployment_links_are_extracted_from_readme():
    readme = """
    [build badge](https://github.com/a/b/actions)
    Live Demo: https://custom.example/app
    screenshot: https://opengraph.githubassets.com/image
    https://sample.vercel.app
    """
    assert deployment_urls(readme) == ["https://custom.example/app", "https://sample.vercel.app"]
