# Sniffing Report

## Summary

- **Total Files**: {{ results.summary.total_files }}
- **Total Issues**: {{ results.summary.total_issues }}
- **Total Fixes**: {{ results.summary.total_fixes }}

{% for domain, domain_data in results.domains.items() %}
## {{ domain|title }}

### Metrics

{% for metric_name, metric_value in domain_data.metrics.items() %}
- **{{ metric_name|replace('_', ' ')|title }}**: {{ metric_value }}
{% endfor %}

### Files

{% for file in domain_data.files %}
#### {{ file.path }}

{% if file.issues %}
##### Issues

{% for issue in file.issues %}
- **{{ issue.title }}** ({{ issue.severity|title }})
  - Description: {{ issue.description }}
  {% if issue.fix %}
  - Fix:
    ```{{ file.path|split('.')|last }}
    {{ issue.fix }}
    ```
  {% endif %}
{% endfor %}
{% endif %}

{% if file.metrics %}
##### Metrics

{% for metric_name, metric_value in file.metrics.items() %}
- **{{ metric_name|replace('_', ' ')|title }}**: {{ metric_value }}
{% endfor %}
{% endif %}

{% endfor %}
{% endfor %}

---
*Generated at: {{ generated_at }}*
