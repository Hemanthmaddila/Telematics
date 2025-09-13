@echo off
echo Creating telematics database and user...
echo You will be prompted for the postgres user password twice.

REM Create the telematics database and user
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE telematics;" 
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create database. You may need to enter the postgres password.
    pause
    exit /b 1
)

"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE USER telematics_admin WITH PASSWORD 'Hemanth13';"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create user. You may need to enter the postgres password.
    pause
    exit /b 1
)

"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE telematics TO telematics_admin;"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to grant privileges. You may need to enter the postgres password.
    pause
    exit /b 1
)

echo Database setup completed successfully!
pause