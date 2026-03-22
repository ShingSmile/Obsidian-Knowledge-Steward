

set -ex



email_validator blah@blah.com
pytest --cov=email_validator
exit 0
