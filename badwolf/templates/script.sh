set +e
echo {{ command }} | base64 --decode | /bin/sh -e
SCRIPT_EXIT_CODE=$?
set -e
{% if after_success -%}
if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    {{ after_success }}
fi
{%- endif %}
{% if after_failure -%}
if [ $SCRIPT_EXIT_CODE -ne 0 ]; then
    {{ after_failure }}
fi
{%- endif %}
exit $SCRIPT_EXIT_CODE
