# Sniffing Report

Generated on {{ data.timestamp }}

## Summary

- Total Files: {{ data.summary.total_files }}
- Total Issues: {{ data.summary.total_issues }}
- Total Fixes: {{ data.summary.total_fixes }}

### Domain Summary

{% for domain, stats in data.summary.domains.items() %}
- {{ domain }}: {{ stats.files }} files, {{ stats.issues }} issues
{% endfor %}

{% for domain, domain_data in data.domains.items() %}
## {{ domain }}

### Metrics

{% for metric_name, metric_value in domain_data.metrics.items() %}
- {{ metric_name }}: {{ metric_value }}
{% endfor %}

### Issues

{% for issue in domain_data.issues %}
#### {{ issue.description }}

- Severity: {{ issue.severity }}
{% if issue.file %}
- File: {{ issue.file }}
{% endif %}
{% if issue.line %}
- Line: {{ issue.line }}
{% endif %}
{% if issue.code %}
```
{{ issue.code }}
```
{% endif %}
{% if issue.fix_suggestion %}
- Fix Suggestion: {{ issue.fix_suggestion }}
{% endif %}

{% endfor %}
{% endfor %}
