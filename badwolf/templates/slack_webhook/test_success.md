:sparkles: <{{ build_log_url }}|Test succeed for repository {{ context.repository }}>

*Repository*: <https://bitbucket.org/{{ context.repository }}|{{ context.repository }}>
*Branch*: <https://bitbucket.org/{{ context.repository }}/src?at={{ branch }}|{{ branch }}>
{% if context.type == 'commit' -%}
*Commit*: <https://bitbucket.org/{{ context.repository }}/commits/{{ context.source.commit.hash }}|{{ context.source.commit.hash }}>
{{ context.message }}
{%- endif %}
{% if context.type == 'pullrequest' -%}
*Pull Request*: <https://bitbucket.org/{{ context.repository }}/pull-requests/{{ context.pr_id }}|{{ context.message }}>
{%- endif %}
