



email_validator blah@blah.com
IF %ERRORLEVEL% NEQ 0 exit /B 1
pytest --cov=email_validator
IF %ERRORLEVEL% NEQ 0 exit /B 1
exit /B 0
